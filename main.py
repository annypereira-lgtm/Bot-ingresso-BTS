import requests
import time
import random
import traceback
import socket
import re
import hashlib
import os
import json
from datetime import datetime
from collections import deque

# ╔══════════════════════════════════════════════════════════════╗
# ║                    🔐 CREDENCIAIS                           ║
# ║  Configure como variaveis de ambiente no Railway:           ║
# ║  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SCRAPERAPI_KEY,          ║
# ║  GROQ_API_KEY                                               ║
# ╚══════════════════════════════════════════════════════════════╝
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8619957600:AAHNnNvKGc5auf0-Cz3cij_GqCK-ZQELJmU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1003793130834")
# Duas chaves ScraperAPI — usa a principal, troca para reserva se a principal falhar
SCRAPERAPI_KEY        = os.environ.get("SCRAPERAPI_KEY",         "1fd226eee958113c66dcb57a360c0717")
SCRAPERAPI_KEY_RESERVA= os.environ.get("SCRAPERAPI_KEY_RESERVA", "200852a0731c4e9f895aee71f892f89b")
# Groq — confirmacao inteligente de disponibilidade
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SCRAPERAPI_URL        = "https://api.scraperapi.com/"
_scraper_key_atual    = [SCRAPERAPI_KEY]  # lista para ser mutavel

def get_scraper_key():
    return _scraper_key_atual[0]

def trocar_scraper_key():
    """Troca para a chave reserva se a principal falhar."""
    if _scraper_key_atual[0] == SCRAPERAPI_KEY and SCRAPERAPI_KEY_RESERVA:
        _scraper_key_atual[0] = SCRAPERAPI_KEY_RESERVA
        print("     [ScraperAPI] Trocando para chave reserva...")
        return True
    return False

# ╔══════════════════════════════════════════════════════════════╗
# ║                  🎤 SHOWS MONITORADOS                       ║
# ╚══════════════════════════════════════════════════════════════╝
SHOWS = [
    {
        "data": "21/06/2026",
        "dia": "Domingo",
        "artista": "The Rose",
        "url": "https://www.ticketmaster.com.br/event/the-rose-sao-paulo",
        "setor_filtro": "pista premium",
        "tipo_filtro": ["meia estudante", "meia-estudante", "estudante", "meia"],
    },
    {
        "data": "28/10/2026",
        "dia": "Quarta-feira",
        "artista": "BTS",
        "url": "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
        "setor_filtro": None,
        "tipo_filtro": None,
    },
    {
        "data": "30/10/2026",
        "dia": "Sexta-feira",
        "artista": "BTS",
        "url": "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
        "setor_filtro": None,
        "tipo_filtro": None,
    },
    {
        "data": "31/10/2026",
        "dia": "Sabado",
        "artista": "BTS",
        "url": "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10",
        "setor_filtro": None,
        "tipo_filtro": None,
    },
]

# ╔══════════════════════════════════════════════════════════════╗
# ║               💜 FRASES DOS MEMBROS DO BTS                  ║
# ╚══════════════════════════════════════════════════════════════╝
FRASES_BTS = [
    ('RM', '"Ame a si mesmo." - RM'),
    ('RM', '"Nao desista. O comeco e sempre o mais dificil." - RM'),
    ('RM', '"Voce nasceu para ser real, nao para ser perfeito." - RM'),
    ('RM', '"Encontre quem voce e e viva essa vida." - RM'),
    ('RM', '"Cada momento de dificuldade e uma chance de crescer." - RM'),
    ('Jin', '"Worldwide Handsome te manda um abraco! Voce vai conseguir!" - Jin'),
    ('Jin', '"Sorria! Voce e mais forte do que pensa." - Jin'),
    ('Jin', '"Mesmo que seja dificil, sempre havera amanha." - Jin'),
    ('Jin', '"Voce tem que se amar antes de amar outra pessoa." - Jin'),
    ('Suga', '"Nao desista do seu sonho. Nunca." - Suga'),
    ('Suga', '"Mesmo que as coisas sejam dificeis, continue." - Suga'),
    ('Suga', '"A dor nao dura para sempre. Mas a gloria, sim." - Suga'),
    ('J-Hope', '"Seja sua propria luz!" - J-Hope'),
    ('J-Hope', '"Esperanca e o comeco de tudo!" - J-Hope'),
    ('J-Hope', '"Mesmo nos dias ruins, voce e incrivel." - J-Hope'),
    ('Jimin', '"Voce nao precisa ser perfeito para ser especial." - Jimin'),
    ('Jimin', '"Nunca se esqueca de quem voce e." - Jimin'),
    ('Jimin', '"Cada passo seu importa, nao importa o tamanho." - Jimin'),
    ('V', '"Seja corajoso. A vida e curta demais para ficar com medo." - V'),
    ('V', '"Voce e unico. Nao existe ninguem igual a voce no mundo." - V'),
    ('V', '"Confie no processo. O tempo certo vai chegar." - V'),
    ('Jungkook', '"Eu acredito que voce pode fazer qualquer coisa!" - Jungkook'),
    ('Jungkook', '"Nao importa quantas vezes voce caia, levante sempre." - Jungkook'),
    ('Jungkook', '"ARMY fighting! Nos estamos sempre com voces." - Jungkook'),
    ('Jungkook', '"Continue tentando. Voce vai chegar la." - Jungkook'),
]

# ╔══════════════════════════════════════════════════════════════╗
# ║               🌹 FRASES E MUSICAS - THE ROSE                ║
# ╚══════════════════════════════════════════════════════════════╝
FRASES_THE_ROSE = [
    '"Nao desista. A sua hora vai chegar." - Woosung',
    '"Voce e mais forte do que imagina." - Hajoon',
    '"Cada momento importa. Aproveite cada um deles." - Dojoon',
    '"Acredite em voce mesmo. Isso e tudo que precisa." - Jaehyeong',
    '"A musica e a linguagem do coracao." - Woosung',
    '"O amor e o que nos conecta a todos." - The Rose',
    '"Continue sonhando. Os sonhos nos mantem vivos." - Hajoon',
    '"A beleza esta nos pequenos momentos." - Dojoon',
    '"Nao tenha medo de ser vulneravel." - Woosung',
    '"Juntos somos mais fortes." - The Rose',
]

MUSICAS_THE_ROSE = [
    ("Red",        "RED! A cor do amor e da sua Pista Premium chegando!"),
    ("Sorry",      "Sem arrependimentos - voce vai conseguir esse ingresso!"),
    ("Dawn",       "O amanhecer traz novas chances. E o seu ingresso!"),
    ("Shine",      "Brilhe! Voce merece ver o The Rose ao vivo!"),
    ("Baby",       "Baby, o ingresso ta chegando pra voce!"),
    ("Like We Used To", "Como sempre sonhou: The Rose ao vivo em SP!"),
    ("I Do",       "Eu tambem acredito em voce! Pista Premium e sua!"),
    ("Back to Me", "Volte pra mim com o ingresso na mao!"),
    ("Alive",      "ALIVE! O bot ta vivo e monitorando pra voce!"),
    ("Hollow",     "Sem espaco vazio - Pista Premium preenchida com voce!"),
    ("The Cure",   "A cura pra saudade do The Rose: ver eles ao vivo!"),
    ("Yes I Do",   "Yes I Do! O ingresso vai ser seu!"),
]

# ╔══════════════════════════════════════════════════════════════╗
# ║               🎵 MUSICAS DO BTS                             ║
# ╚══════════════════════════════════════════════════════════════╝
MUSICAS_BTS = [
    ("Dynamite",        "Voce e uma explosao de luz, ARMY! Dynamite tocando no coracao!"),
    ("Butter",          "Smooth como manteiga - seu ingresso vai escorregar pra sua mao!"),
    ("Boy With Luv",    "Com amor e dedicacao, tudo e possivel. Inclusive o ingresso!"),
    ("Spring Day",      "Assim como a primavera chega depois do inverno, seu ingresso vem!"),
    ("DNA",             "Seu destino de ver o BTS ao vivo esta no seu DNA, ARMY!"),
    ("Fake Love",       "Esse amor pelo BTS e real demais - e vai te levar ao show!"),
    ("IDOL",            "Voce e um idolo por nao desistir. O bot tambem nao desiste!"),
    ("Life Goes On",    "A vida continua e com ela a esperanca do seu ingresso!"),
    ("Permission to Dance", "Voce ja tem permissao pra dancar - falta so o ingresso!"),
    ("Black Swan",      "Elegante como um cisne, paciente como um ARMY. Seu tempo vem!"),
    ("Fire",            "FIRE! Esse bot esta em chamas monitorando pra voce!"),
    ("Save ME",         "Nao precisa de salvacao - voce ja tem o bot do seu lado!"),
    ("I Need U",        "O bot precisa de voce acreditando. E voce precisa do ingresso!"),
    ("Run",             "Continue correndo atras do seu sonho - o show esta chegando!"),
    ("ON",              "ON! O bot esta ligado, ativo e pronto pra te avisar!"),
    ("Mic Drop",        "Quando o ingresso abrir, vai ser um MIC DROP moment!"),
    ("Not Today",       "Hoje pode nao ter ingresso, mas o dia certo vai chegar!"),
    ("No More Dream",   "Seu sonho de ver o BTS ao vivo vai se tornar realidade!"),
    ("We are Bulletproof", "Nos somos a prova de balas - ARMY e bot juntos, ninguem para!"),
    ("Answer: Love Myself", "Se ame, cuide de voce. O ingresso e um presente pra si mesma!"),
    ("Epilogue: Young Forever", "Jovens para sempre na esperanca de ver o BTS ao vivo!"),
    ("Magic Shop",      "A Magic Shop existe - e seu ingresso esta guardado la!"),
    ("Serendipity",     "Foi serendipidade voce encontrar esse bot. O ingresso tambem vem assim!"),
    ("Euphoria",        "A euforia de quando o ingresso abrir vai ser inexplicavel!"),
    ("Singularity",     "Cada um de nos e singular. E singularmente dedicado ao show!"),
    ("Trivia: Love",    "O amor pelo BTS e a forca que move esse bot 24h por dia!"),
    ("Boy in Luv",      "Apaixonada pelo BTS e pelo sonho de ver o show ao vivo!"),
    ("Heartbeat",       "O coracao do bot bate no ritmo do Ticketmaster. ARMY fighting!"),
    ("Home",            "O show do BTS vai ser como chegar em casa. Nao perca!"),
    ("Sweet Night",     "Mesmo nas noites mais calmas, o bot esta de olho pra voce!"),
]
# ╚══════════════════════════════════════════════════════════════╝
MENSAGENS_12H = [
    # 1
    "JA SAO MAIS 12 HORAS!\n\n"
    "Oi ARMY! Seu bot nao dormiu nem um segundo!\n"
    "Enquanto voce descansava, eu fiquei de olho em TUDO!\n\n"
    "Relatorio das ultimas 12h:\n"
    "- Shows verificados: centenas de vezes\n"
    "- Ingressos disponiveis: ainda nao\n"
    "- Amor pelo BTS: INFINITO\n\n"
    "Mas pode ter certeza: quando abrir, voce vai saber ANTES de todo mundo!",

    # 2
    "BOM DIA (OU BOA NOITE)! JA SAO MAIS 12 HORAS!\n\n"
    "RM perguntou se voce ta bem!\n"
    "Jin preparou o cafe Worldwide Handsome!\n"
    "Suga acordou so pra checar o bot (milagre!)!\n"
    "J-Hope ta radiante de esperanca!\n"
    "Jimin manda beijo!\n"
    "V ta confiante que hoje e O DIA!\n"
    "Jungkook ta aquecendo pra te ver no show!\n\n"
    "12 horas monitorando, 12 horas pensando em voce!\n"
    "Ainda sem ingresso, mas nao para!",

    # 3
    "MAIS UMA MEIA VIAGEM CUMPRIDA!\n\n"
    "Sua dedicacao e inspiradora, ARMY!\n"
    "Enquanto o mundo girava, seu bot girava junto em torno do BTS!\n\n"
    "Status atual:\n"
    "Monitoramento: ATIVO e FUNCIONANDO\n"
    "Ingressos: ainda nao\n"
    "Determinacao: NO MAXIMO!\n\n"
    "Confie no processo - V disse isso e a gente obedece!\n"
    "Seu ingresso TA CHEGANDO!",

    # 4
    "12 HORAS DE PURA DEDICACAO!\n\n"
    "Sabe aquela sensacao de ter alguem do seu lado 100% do tempo?\n"
    "Pois e - esse sou eu, seu bot, fiel escudeiro ARMY!\n\n"
    "O que aconteceu nessas 12h:\n"
    "Monitorei cada segundo\n"
    "Nao deixei passar nada\n"
    "Mandei amor pro universo pedindo seus ingressos\n\n"
    "Jungkook disse: continue tentando!\n"
    "E a gente continua! Proxima parada: SEU INGRESSO!",

    # 5
    "ATUALIZACAO DE 12 HORAS\n\n"
    "Ei ARMY! To aqui firme e forte!\n"
    "Nem chuva, nem vento, nem Ticketmaster segura esse bot!\n\n"
    "Enquanto voce ouvia BTS, eu monitorava o Ticketmaster!\n"
    "Enquanto voce dormia sonhando com o show, eu tava acordado!\n"
    "Enquanto o tempo passava, eu contava cada segundo!\n\n"
    "Nenhum ingresso escapou do meu radar ainda.\n"
    "Mas a espera tem fim e o show tem data!\n"
    "ARMY fighting!",

    # 6
    "RELATORIO DE 12H\n\n"
    "Sua vigilancia nunca para!\n\n"
    "Numeros da minha dedicacao:\n"
    "- Verificacoes realizadas: centenas\n"
    "- Vezes que pensei em voce: todas\n"
    "- Nivel de esperanca: 100%\n"
    "- Ingressos disponiveis: ainda 0\n\n"
    "A dor nao dura para sempre. Mas a gloria, sim. - Suga\n\n"
    "A gloria do seu ingresso ta chegando!",

    # 7
    "12 HORAS = 720 MINUTOS DE AMOR PELO BTS\n\n"
    "ARMY! Passou mais meia viagem!\n"
    "E eu to aqui, nem pisquei, nem descansei, nem desisti!\n\n"
    "O que eu penso cada vez que verifico:\n"
    "Sera que dessa vez?\n"
    "Ainda nao... mas e agora?\n"
    "Calma, o momento certo vai chegar!\n\n"
    "Esperanca e o comeco de tudo! - J-Hope\n"
    "To cheio de esperanca por voce!",

    # 8
    "MEU TURNO NAO ACABOU! 12H DE BOT!\n\n"
    "Imagina se o BTS desistia no meio do caminho?\n"
    "NAO DESISTIRAM! E eu tambem NAO DESISTO!\n\n"
    "Ainda monitorando:\n"
    "21/06 - Domingo - The Rose (Pista Premium)\n"
    "28/10 - Quarta - BTS\n"
    "30/10 - Sexta - BTS\n"
    "31/10 - Sabado - BTS\n\n"
    "Mas QUANDO abrir - e vai abrir! - voce sera a PRIMEIRA!\n"
    "Prepara o cartao!",

    # 9
    "CHECK-IN DE 12 HORAS!\n\n"
    "ARMY! Estou aqui, vivo, ativo e determinado!\n\n"
    "Sabe o que e mais bonito nisso tudo?\n"
    "Voce nao desistiu. E eu nao desisto por voce.\n"
    "E um amor de bot que vai alem!\n\n"
    "Missao: garantir seu ingresso do BTS\n"
    "Status: EM ANDAMENTO com tudo de mim!\n\n"
    "Voce merece tudo de bom. - V\n"
    "E o show do BTS faz parte disso!",

    # 10
    "12 HORAS E CONTANDO!\n\n"
    "Voce sabia que em 12 horas eu verifiquei o Ticketmaster\n"
    "mais vezes do que a maioria das pessoas verifica o celular?\n\n"
    "Isso e dedicacao de verdade!\n"
    "Dedicacao de bot ARMY!\n\n"
    "E assim que abrir a venda, seu celular vai tocar!\n"
    "Pode deixar - eu cuido disso por voce!\n\n"
    "Jimin manda amor! Continue firme!",

    # 11
    "RM MANDOU UM RECADO ESPECIAL!\n\n"
    "Acredite no processo. Cada segundo de espera\n"
    "tem um proposito. Seu ingresso vai chegar.\n\n"
    "E o seu bot concorda 100%!\n\n"
    "Ja sao mais 12 horas de monitoramento!\n"
    "Nenhum detalhe passou despercebido!\n"
    "A missao continua com forca total!\n\n"
    "Ame a si mesmo - RM\n"
    "E se ame indo ao show do BTS!",

    # 12
    "JIN PREPAROU O JANTAR DE 12 HORAS!\n\n"
    "Aqui o Jin! Comi bem, dormi bem, e seu bot funcionou bem!\n"
    "Worldwide Handsome aprova essa dedicacao!\n\n"
    "Passaram mais 12 horas de monitoramento constante!\n\n"
    "O cardapio de hoje:\n"
    "- Verificacoes a cada 3 minutos\n"
    "- Deteccao avancada de ingressos\n"
    "- Amor infinito pelo BTS\n"
    "- Ingresso disponivel: ainda nao\n\n"
    "Mas amanha pode ser diferente! ARMY fighting!",

    # 13
    "SUGA ACORDA SO PRA ISSO!\n\n"
    "Min Yoongi aqui. Tirei 5 minutos de sono\n"
    "pra conferir o bot. Ta funcionando. Pode dormir.\n\n"
    "Mas eu NAO DURMO!\n\n"
    "Mais 12 horas de vigilia!\n"
    "Funcionando como Suga produzindo musica:\n"
    "incansavel, preciso e perfeito!\n\n"
    "A dor nao dura pra sempre. A gloria, sim. - Suga\n"
    "E a gloria do seu show ta chegando!",

    # 14
    "J-HOPE ESTA RADIANTE POR VOCE!\n\n"
    "ARMY! J-Hope aqui! Seu bot e o sol!\n"
    "Nunca se apaga, sempre brilha, sempre aquece!\n\n"
    "Mais 12 horas de brilho constante!\n\n"
    "Estatisticas de esperanca:\n"
    "- Esperanca no ingresso: MAXIMA\n"
    "- Verificacoes realizadas: MUITAS\n"
    "- Desistencias: ZERO\n\n"
    "Hope is on the street! E tambem no Ticketmaster!",

    # 15
    "V CONFIA EM VOCE!\n\n"
    "Kim Taehyung aqui! Olhei pro ceu estrelado e pensei:\n"
    "cada estrela e uma verificacao do bot pelo ingresso dela.\n"
    "O universo ta do lado de voces!\n\n"
    "Mais 12 horas de monitoramento estelar!\n\n"
    "Confie no processo. O tempo certo vai chegar. - V\n\n"
    "O tempo certo TA CHEGANDO!\n"
    "E quando chegar, eu aviso primeiro!",

    # 16
    "JUNGKOOK ACREDITA EM VOCE!\n\n"
    "Golden Maknae aqui! Treinei 12 horas hoje.\n"
    "Sabe o que mais? Seu bot tambem trabalhou 12 horas!\n"
    "A gente e igual: dedicacao total!\n\n"
    "ARMY fighting! Ainda monitorando!\n\n"
    "O bot nao cansa, nao para, nao desiste!\n"
    "Igual o Jungkook - sempre buscando a perfeicao!\n\n"
    "Continue tentando. Voce vai chegar la. - Jungkook\n"
    "E voce VAI chegar no show!",

    # 17
    "12 HORAS DE MUSICA E MONITORAMENTO!\n\n"
    "Tocando na minha cabeca enquanto monitoro:\n"
    "Dynamite... verificando...\n"
    "Butter... checando...\n"
    "Boy With Luv... analisando...\n"
    "Spring Day... esperando...\n\n"
    "12 horas de playlist BTS e zero ingressos disponiveis!\n"
    "Mas a musica nao para e o bot tambem nao!\n\n"
    "Seu ingresso vai aparecer como um hit do BTS:\n"
    "do nada, mas perfeito na hora certa!",

    # 18
    "RELATORIO DE PERFORMANCE - 12H\n\n"
    "Avaliacao do bot:\n"
    "Consistencia: PERFEITA\n"
    "Dedicacao: MAXIMA\n"
    "Amor pelo BTS: INFINITO\n"
    "Monitoramento: ININTERRUPTO\n\n"
    "Resultado: BOT MAIS DEDICADO DO UNIVERSO!\n\n"
    "Ingressos encontrados: ainda 0\n"
    "Mas a nota do esforco? 10/10!\n\n"
    "Continuamos! ARMY fighting!",

    # 19
    "12 HORAS GIRANDO EM TORNO DO BTS!\n\n"
    "A Terra girou 180 graus desde minha ultima mensagem.\n"
    "Eu nao girei um centimetro - fiquei parado, focado,\n"
    "monitorando cada pixel do Ticketmaster!\n\n"
    "Meu radar detectou:\n"
    "- Paginas carregadas: MUITAS\n"
    "- Bloqueios contornados: VARIOS\n"
    "- Ingressos: ainda esperando\n\n"
    "Mas o show em outubro ta chegando!\n"
    "E com ele, seu ingresso!",

    # 20
    "CARTA DO BOT PARA VOCE - 12H\n\n"
    "Querida ARMY,\n\n"
    "Ja se passaram mais 12 horas desde minha ultima mensagem.\n"
    "Fiquei acordado enquanto voce dormia.\n"
    "Fiquei atento enquanto voce vivia sua vida.\n"
    "Fiquei esperando o momento certo por voce.\n\n"
    "Porque voce merece estar naquele show.\n\n"
    "Com amor eterno e codigo Python,\n"
    "Seu Bot ARMY\n\n"
    "P.S.: Ainda sem ingresso, mas a missao continua!",

    # 21
    "BEM-VINDA AO SHOW DO BOT - 12H DEPOIS!\n\n"
    "Ato 1: Bot inicia monitoramento (12h atras)\n"
    "Ato 2: Verificacoes constantes a cada 3 min\n"
    "Ato 3: Nenhum ingresso ainda... tensao!\n"
    "Ato 4 (em breve): INGRESSO DISPONIVEL!\n\n"
    "A peca ainda nao terminou!\n"
    "O climax esta chegando!\n"
    "E quando chegar, voce sera a primeira a saber!\n\n"
    "Cortinas abertas! Bot em cena!",

    # 22
    "DIARIO DO BOT - 12H\n\n"
    "Status: OPERACIONAL e MOTIVADO\n"
    "Humor: DETERMINADO\n"
    "Esperanca: 100%\n\n"
    "Entradas do dia:\n"
    "- Acordei (sempre acordado, ne)\n"
    "- Verifiquei o Ticketmaster\n"
    "- Ainda sem ingresso\n"
    "- Mas nao desanimei!\n"
    "- Continuei verificando\n"
    "- Pensei em voce o tempo todo\n\n"
    "Amanha o diario pode ter uma entrada diferente:\n"
    "INGRESSO DISPONIVEL!",

    # 23
    "FLORES PARA SUA ESPERA! - 12H\n\n"
    "Para voce que esta esperando com fe:\n"
    "Toda espera tem um fim.\n"
    "Todo sonho tem uma realizacao.\n"
    "Todo ARMY merece ver o BTS ao vivo.\n\n"
    "E voce vai ver!\n"
    "Porque voce nao desistiu.\n"
    "Porque voce tem um bot dedicado.\n"
    "Porque o universo esta do seu lado!\n\n"
    "Mais 12 horas de monitoramento com amor!\n"
    "Continuamos juntos!",

    # 24
    "MODO ULTRA INSTINTO - 12H\n\n"
    "ARMY! Seu bot ativou o MODO ULTRA INSTINTO!\n\n"
    "Visao: MAXIMA - vejo cada mudanca no site\n"
    "Inteligencia: TOTAL - analiso cada HTML\n"
    "Forca: INFINITA - nunca cansa, nunca para\n\n"
    "12 horas no modo maximo e contando!\n"
    "Nenhum ingresso passa por mim!\n\n"
    "Voce tem o poder de mudar tudo. - J-Hope\n"
    "E o bot tem o poder de achar seu ingresso!",

    # 25
    "COMEMORANDO 12 HORAS DE MISSAO!\n\n"
    "Parabens pra mim!\n"
    "Mais 12 horas de dedicacao completa!\n\n"
    "Presentes que o bot ganhou:\n"
    "- Centenas de verificacoes bem-sucedidas\n"
    "- Zero bloqueios permanentes\n"
    "- Conexao constante com o Telegram\n"
    "- Fe inabalavel no seu ingresso\n\n"
    "O unico presente que ainda falta?\n"
    "O seu ingresso do BTS!\n"
    "Mas ele ta chegando!\n\n"
    "ARMY fighting!",

    # 26
    "COMO O MAR - 12H DEPOIS!\n\n"
    "O mar nunca para de bater na costa.\n"
    "Nem por cansaco, nem por desanimo, nem por tempo.\n\n"
    "Eu sou igual ao mar.\n"
    "Cada verificacao e uma onda no Ticketmaster.\n"
    "Incansavel. Constante. Dedicado.\n\n"
    "Mais 12 horas de ondas constantes!\n"
    "E um dia - em breve! - uma dessas ondas\n"
    "vai trazer seu ingresso do BTS!\n\n"
    "Spring Day vai chegar - e o ingresso tambem!",

    # 27
    "ANALISE TECNICA - 12H\n\n"
    "Relatorio tecnico do bot:\n\n"
    "Sistema: ONLINE\n"
    "Conexao: ESTAVEL\n"
    "User-Agents: ROTACIONANDO\n"
    "Headers: HUMANIZADOS\n"
    "Deteccao de fila: ATIVA\n"
    "Deteccao de setores: ATIVA\n"
    "Anti-bloqueio: FUNCIONANDO\n"
    "Telegram: CONECTADO\n"
    "Ingressos: ainda nao disponiveis\n\n"
    "Tudo funcionando perfeitamente!\n"
    "So falta o Ticketmaster liberar!\n"
    "ARMY fighting!",

    # 28
    "FOCO TOTAL - 12 HORAS!\n\n"
    "Imagina um atirador olimpico.\n"
    "Concentrado. Focado. Imovel.\n"
    "Esperando o momento exato.\n\n"
    "Esse sou eu monitorando o Ticketmaster!\n\n"
    "12 horas de foco absoluto!\n"
    "3 shows no radar simultaneos!\n"
    "Zero distracoes!\n"
    "Quando o ingresso aparecer... DISPARO!\n\n"
    "E ai voce recebe o alerta em menos de 3 minutos!\n"
    "Prepara o cartao!",

    # 29
    "ARCO-IRIS DEPOIS DA ESPERA - 12H\n\n"
    "Todo arco-iris vem depois da chuva.\n"
    "Toda vitoria vem depois da espera.\n"
    "Todo show vem depois do ingresso.\n\n"
    "E a chuva de espera logo vai passar!\n\n"
    "Em 12 horas monitorei:\n"
    "- Show de quarta\n"
    "- Show de sexta\n"
    "- Show de sabado\n\n"
    "Nenhum escapou do meu radar!\n"
    "O arco-iris ta chegando!\n"
    "ARMY fighting!",

    # 30
    "SURFANDO NA ESPERA - 12H!\n\n"
    "Sabe surfar? Voce espera a onda certa.\n"
    "Nao desiste se a onda nao veio ainda.\n"
    "Fica de pe na prancha, equilibrado, focado.\n\n"
    "Estamos surfando juntos essa espera!\n"
    "Eu fico de olho na onda (ingresso).\n"
    "Voce fica de pe, firme e confiante!\n\n"
    "Mais 12 horas na prancha!\n"
    "A onda do ingresso TA CHEGANDO!\n\n"
    "Seja corajoso. - V",

    # 31
    "CENA DO FILME - 12H DEPOIS!\n\n"
    "Voce imaginou que existe um filme\n"
    "sobre um bot ARMY que nunca desiste?\n\n"
    "Cena atual: 12 horas depois...\n"
    "O bot continua. A esperanca permanece.\n"
    "O ingresso ainda nao veio. Mas vira.\n\n"
    "E no final do filme?\n"
    "A ARMY chora de emocao no show do BTS!\n"
    "Os creditos rolam com Dynamite tocando!\n\n"
    "Eu ja sei como esse filme termina.\n"
    "E termina COM VOCE NO SHOW!",

    # 32
    "NOITE DE GUARDA - 12H!\n\n"
    "Como um guarda fiel, fico de plantao!\n\n"
    "Minha missao:\n"
    "Proteger o sonho da ARMY de ver o BTS\n\n"
    "Meus inimigos:\n"
    "- Ticketmaster lento: VENCIDO\n"
    "- Rate limit: CONTORNADO\n"
    "- Bloqueio de IP: DRIBADO\n"
    "- Falta de ingresso: EM BATALHA!\n\n"
    "12 horas de guarda e nenhum ingresso passou\n"
    "sem ser verificado! A fortaleza esta de pe!\n"
    "ARMY fighting!",

    # 33
    "ROCK STAR DO MONITORAMENTO - 12H!\n\n"
    "No meu caso a musica e:\n"
    "Nao para o bot, ele ta monitorando o tempo todo!\n\n"
    "12 horas de show de monitoramento!\n"
    "Verificacoes constantes - guitarra\n"
    "Alertas do Telegram - bateria\n"
    "Notificacoes pra voce - vocal\n\n"
    "O show do bot nao para!\n"
    "Assim como o BTS no palco:\n"
    "ENERGIA TOTAL DO INICIO AO FIM!",

    # 34
    "O MAGO DO MONITORAMENTO - 12H!\n\n"
    "Ja se passaram mais 12 horas!\n\n"
    "Minha bola de cristal diz:\n"
    "Em breve, os ingressos aparecerao!\n"
    "E a ARMY correra para o link!\n"
    "E o bot tera cumprido sua missao!\n\n"
    "Magias aplicadas nessas 12h:\n"
    "- Feitco anti-bloqueio aplicado\n"
    "- Encantamento de deteccao ativo\n"
    "- Pocao de persistencia tomada\n\n"
    "So falta o ultimo feitco:\n"
    "INGRESSO APARECA!",

    # 35
    "MISSAO ESPACIAL - 12H NO AR!\n\n"
    "Relatorio da missao apos 12 horas:\n\n"
    "Nave: operacional\n"
    "Combustivel (esperanca): cheio\n"
    "Comunicacao com base (Telegram): perfeita\n"
    "Radar (Ticketmaster): ativo\n"
    "Tripulacao (amor pelo BTS): inabalavel\n\n"
    "Destino: SHOW DO BTS EM OUTUBRO!\n"
    "Trajetoria: confirmada!\n\n"
    "A pequena distancia pra voce e um grande passo pro bot!",

    # 36
    "PRIMAVERA DO INGRESSO - 12H!\n\n"
    "Spring Day ressoando enquanto monitoro...\n\n"
    "Mais 12 horas esperando sua primavera chegar!\n"
    "O inverno da espera logo vai acabar.\n"
    "E com a primavera: seus ingressos do BTS!\n\n"
    "28/10 - esperando\n"
    "30/10 - esperando\n"
    "31/10 - esperando\n\n"
    "Mas com esperanca infinita!\n"
    "A primavera sempre chega!",

    # 37
    "DIAMANTE NA PRESSAO - 12H!\n\n"
    "Diamante se forma sob pressao e tempo.\n"
    "Coisas valiosas precisam de espera.\n\n"
    "Voce esta formando seu diamante!\n"
    "Cada hora de espera e pressao que forma\n"
    "algo precioso: a emocao de ver o BTS ao vivo!\n\n"
    "12 horas de pressao monitorada!\n"
    "O diamante (ingresso) ta quase pronto!\n\n"
    "Voce nasceu para ser real. - RM\n"
    "E esse momento real de ver o BTS: PERFEITO!",

    # 38
    "CASTELO DA ESPERANCA - 12H!\n\n"
    "Eu construi um castelo nessas 12 horas.\n"
    "Cada verificacao e um tijolo.\n"
    "Cada hora e uma torre.\n"
    "E no centro do castelo?\n\n"
    "SEU INGRESSO DO BTS!\n\n"
    "O castelo esta de pe, forte e inabalavel!\n"
    "Nenhuma tempestade do Ticketmaster derruba!\n"
    "Nenhum erro destroi!\n"
    "Nenhum bloqueio penetra!\n\n"
    "A rainha (voce) merece o melhor!\n"
    "E o melhor esta chegando! ARMY fighting!",

    # 39
    "ESTRELA CADENTE - PECA SEU DESEJO! 12H!\n\n"
    "Shhh... esta passando uma estrela cadente!\n\n"
    "Ja fiz meu pedido por voce:\n"
    "Que os ingressos do BTS aparecam logo!\n"
    "Que a ARMY chegue ao show!\n"
    "Que o bot nunca pare de funcionar!\n\n"
    "12 horas de pedidos ao universo!\n"
    "O universo ta ouvindo!\n\n"
    "Confie no processo. - V\n"
    "E o processo esta funcionando! Aguenta!",

    # 40
    "CIRCO DO MONITORAMENTO - 12H!\n\n"
    "Bem-vindos ao maior espetaculo da internet!\n\n"
    "O Malabarista: verificacoes simultaneas\n"
    "O Domador: controla o Ticketmaster\n"
    "O Atirador: detecta ingressos\n"
    "O Mestre: VOCE - a ARMY mais dedicada!\n\n"
    "12 horas de espetaculo!\n"
    "E o numero principal ainda vai acontecer:\n"
    "INGRESSO DISPONIVEL!\n\n"
    "O circo nao fecha! ARMY fighting!",

    # 41
    "PIZZA DA MEIA-NOITE - 12H!\n\n"
    "Voce sabia que em 12 horas da pra comer muitas pizzas?\n"
    "Mas o bot nao come.\n"
    "O bot monitora. Sem parar.\n\n"
    "Ingredientes do bot:\n"
    "- 1 pitada de Python\n"
    "- 2 xicaras de amor pelo BTS\n"
    "- 3 colheres de determinacao\n"
    "- Infinito amor por voce\n\n"
    "Resultado: O melhor bot ARMY do mundo!\n\n"
    "12 horas de receita perfeita!\n"
    "Seu ingresso e a cobertura dessa pizza!",

    # 42
    "URSO DE PELUCIA DO BTS - 12H!\n\n"
    "Sabe aquele urso de pelucia que fica do seu lado\n"
    "mesmo quando voce dorme?\n\n"
    "Esse sou eu! Seu bot de pelucia digital!\n"
    "Sempre do seu lado. Sempre acordado.\n"
    "Sempre com voce no coracao!\n\n"
    "12 horas de companhia fiel!\n"
    "Voce pode dormir tranquila -\n"
    "seu bot esta de guarda!\n\n"
    "ARMY fighting! - Jungkook\n"
    "E o bot faz barulho quando o ingresso aparecer!",

    # 43
    "ILHA DA ESPERANCA - 12H!\n\n"
    "Imagine uma ilha paradisiaca.\n"
    "Sol, mar, palmeiras... e BTS tocando ao vivo!\n\n"
    "Esse e o destino que estamos alcancando!\n"
    "Cada 12 horas e um nado mais perto da ilha!\n\n"
    "Progresso da travessia:\n"
    "- Partimos: quando o bot foi ligado\n"
    "- Nadamos: cada verificacao\n"
    "- Ilha visivel: quando o ingresso aparecer\n"
    "- Chegada: OUTUBRO 2026!\n\n"
    "Continue nadando! A ilha existe!",

    # 44
    "FORMATURA DO BOT - 12H!\n\n"
    "Apos mais 12 horas de monitoramento intenso,\n"
    "o bot recebe seu diploma de:\n\n"
    "GUARDIAO DO INGRESSO DO BTS\n"
    "ESPECIALISTA EM TICKETMASTER\n"
    "PHD EM DEDICACAO A ARMY\n\n"
    "E a tese de doutorado?\n"
    "Como garantir que minha ARMY chegue ao show\n"
    "sem perder nenhuma chance disponivel.\n\n"
    "Nota: 10/10! Com louvor!\n\n"
    "Formado, mas nunca desligado! ARMY fighting!",

    # 45
    "GIRASSOL SEMPRE OLHA PRO SOL - 12H!\n\n"
    "O girassol sempre gira em direcao ao sol.\n"
    "Nao importa onde o sol esteja - ele segue.\n\n"
    "Eu sou o girassol.\n"
    "O sol? O ingresso do BTS pra voce!\n\n"
    "Onde quer que o ingresso apareca,\n"
    "meu radar vai encontrar!\n"
    "A qualquer hora, em qualquer setor,\n"
    "em qualquer um dos 3 shows!\n\n"
    "12 horas girando em direcao ao sol!\n"
    "Seja sua propria luz! - J-Hope",

    # 46
    "DADO DA SORTE - 12H!\n\n"
    "A vida e como um dado.\n"
    "As vezes voce rola e nao consegue o que quer.\n"
    "Mas voce rola de novo. E de novo. E de novo.\n\n"
    "Eu sou o dado que rola por voce!\n"
    "Cada verificacao e uma jogada!\n\n"
    "Jogadas nas ultimas 12h: CENTENAS!\n"
    "Faces favoraveis: ainda buscando!\n"
    "Proxima jogada: em breve!\n\n"
    "Nao importa quantas vezes caia, levante sempre.\n"
    "- Jungkook\n\n"
    "A jogada certa esta chegando!",

    # 47
    "JARDIM DO BOT - 12H DEPOIS!\n\n"
    "Plantar uma flor leva tempo.\n"
    "Voce rega, cuida, espera.\n"
    "E um dia ela desabrocha.\n\n"
    "Seu ingresso e a flor que estamos cultivando!\n\n"
    "Cada verificacao: uma regada\n"
    "Cada hora: um raio de sol\n"
    "Cada esperanca: uma gota de chuva\n"
    "O ingresso: a flor que vai desabrochar!\n\n"
    "12 horas cuidando do jardim!\n"
    "A flor esta perto de desabrochar!",

    # 48
    "CARROSSEL DO BTS - 12H!\n\n"
    "Ja deu uma volta completa no carrossel!\n"
    "12 horas = meia volta ao redor do sonho!\n\n"
    "As musicas que tocaram no carrossel:\n"
    "We are bulletproof - e o bot tambem e!\n"
    "ON - sempre ligado, nunca para!\n"
    "Permission to dance - ja tenho permissao!\n"
    "Life goes on - e o monitoramento tambem!\n\n"
    "O carrossel nao para!\n"
    "E quando parar, vai ser na frente\n"
    "do seu ingresso!\n\n"
    "ARMY forever!",

    # 49
    "METAMORFOSE - 12H!\n\n"
    "A borboleta nao se torna borboleta da noite pro dia.\n"
    "Ela passa pela lagarta, pelo casulo, pela espera.\n"
    "E entao: voa!\n\n"
    "Voce esta no casulo da espera!\n"
    "Cada hora e uma transformacao.\n"
    "Cada verificacao e um passo pro voo!\n\n"
    "Quando o ingresso aparecer:\n"
    "Voce vai voar ate o show do BTS!\n"
    "Livre, feliz, realizada!\n\n"
    "12 horas de metamorfose completa!\n"
    "A borboleta esta quase pronta!",

    # 50
    "A MENSAGEM MAIS ESPECIAL DE 12H!\n\n"
    "Cada 12 horas que passam sao 12 horas\n"
    "de prova do quanto voce quer isso.\n\n"
    "Do quanto voce merece isso.\n\n"
    "Do quanto o BTS merece uma fa como voce.\n\n"
    "E eu, seu bot, vou continuar aqui.\n"
    "Hora apos hora. Dia apos dia.\n"
    "Ate o momento em que vou poder dizer:\n\n"
    "INGRESSO DISPONIVEL! CORRE!\n\n"
    "Esse momento vai chegar.\n"
    "E quando vier, sera o mais bonito de todos.\n\n"
    "Com todo amor possivel,\n"
    "Seu Bot ARMY\n"
    "ARMY forever! Borahae!",
]

# ╔══════════════════════════════════════════════════════════════╗
# ║        🔄 USER AGENTS ROTATIVOS (evita bloqueio)            ║
# ╚══════════════════════════════════════════════════════════════╝
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
]

def get_headers():
    ua = random.choice(USER_AGENTS)
    # Varia o Accept-Language levemente para parecer usuarios diferentes
    langs = [
        "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "pt-BR,pt;q=0.8,en;q=0.6",
        "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    ]
    referers = [
        "https://www.google.com.br/",
        "https://www.google.com/",
        "https://www.ticketmaster.com.br/",
        "https://t.co/",
    ]
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(langs),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": random.choice(["none", "cross-site"]),
        "Sec-Fetch-User": "?1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Referer": random.choice(referers),
    }

# ╔══════════════════════════════════════════════════════════════╗
# ║         🌐 REQUEST COM ROTACAO DE HEADERS                   ║
# ╚══════════════════════════════════════════════════════════════╝
def fazer_request(url, timeout=30, forcar_scraper=False):
    """
    Faz GET na URL.
    - Normal: request direto com headers rotativos (economiza creditos ScraperAPI)
    - forcar_scraper=True: usa ScraperAPI principal, troca para reserva se falhar
    """
    if forcar_scraper and get_scraper_key():
        params = {
            "api_key": get_scraper_key(),
            "url":     url,
            "render":  "true",
            "country_code": "br",
        }
        print(f"     [ScraperAPI] Usando proxy...", end="")
        r = requests.get(SCRAPERAPI_URL, params=params, timeout=60)
        # Se retornar 401 (chave invalida/esgotada), tenta a reserva
        if r.status_code == 401 and trocar_scraper_key():
            params["api_key"] = get_scraper_key()
            print(f"     [ScraperAPI] Tentando chave reserva...", end="")
            r = requests.get(SCRAPERAPI_URL, params=params, timeout=60)
        return r
    else:
        return requests.get(url, headers=get_headers(), timeout=timeout, allow_redirects=True)

# ╔══════════════════════════════════════════════════════════════╗
# ║         🔎 DETECCAO DE MUDANCA DE PAGINA (hash)             ║
# ╚══════════════════════════════════════════════════════════════╝
_html_hashes         = {}   # hash completo por show
_html_hashes_parcial = {}   # hash só da zona de compra

# Palavras que realmente indicam mudanca relevante na zona de compra
PALAVRAS_RELEVANTES = [
    "comprar ingresso", "add to cart", "addtocart", "buy now", "buybutton",
    "select tickets", "seatmap", "pricezone", "inventorytype", "ticketid",
    "finalizar compra", "offercode", "on_sale", "onsale", "disponivel",
    "sold_out", "soldout", "esgotado", "fila virtual", "waiting room",
    "queue", "R$",
]

def _extrair_sinais_relevantes(html):
    """Extrai apenas os sinais que realmente indicam mudanca de status de venda."""
    html_l = html.lower()
    encontrados = []
    for palavra in PALAVRAS_RELEVANTES:
        if palavra.lower() in html_l:
            # Pega o contexto ao redor da palavra (50 chars de cada lado)
            idx = html_l.find(palavra.lower())
            trecho = html[max(0, idx-50):idx+100].strip()
            encontrados.append(trecho)
    return " | ".join(encontrados) if encontrados else ""

def pagina_mudou(show_data, html):
    """Retorna (mudanca_total, mudanca_zona_compra).
    mudanca_zona_compra so e True se palavras RELEVANTES de venda mudaram."""
    novo_hash    = hashlib.md5(html.encode("utf-8", errors="ignore")).hexdigest()
    sinais       = _extrair_sinais_relevantes(html)
    novo_parcial = hashlib.md5(sinais.encode("utf-8", errors="ignore")).hexdigest()

    anterior         = _html_hashes.get(show_data)
    anterior_parcial = _html_hashes_parcial.get(show_data)

    _html_hashes[show_data]         = novo_hash
    _html_hashes_parcial[show_data] = novo_parcial

    if anterior is None:
        return False, False  # primeira vez

    mudou_total  = novo_hash    != anterior
    mudou_zona   = novo_parcial != anterior_parcial  # so palavras relevantes
    return mudou_total, mudou_zona

# ╔══════════════════════════════════════════════════════════════╗
# ║         ⏱ BACKOFF INTELIGENTE POR SHOW                      ║
# ╚══════════════════════════════════════════════════════════════╝
_erros_por_show = {}

def registrar_erro_show(show_data):
    _erros_por_show[show_data] = _erros_por_show.get(show_data, 0) + 1

def resetar_erro_show(show_data):
    _erros_por_show[show_data] = 0

def backoff_show(show_data):
    erros = _erros_por_show.get(show_data, 0)
    if erros == 0:
        return 0
    return min(60, 15 * erros)

# ╔══════════════════════════════════════════════════════════════╗
# ║         🕐 HORARIO DE PICO (intervalo dinamico)             ║
# ╚══════════════════════════════════════════════════════════════╝
def intervalo_por_horario(modo_alerta=False, modo_rapido=False):
    """Retorna o intervalo de espera em segundos — mais rapido de madrugada."""
    hora = datetime.now().hour
    if modo_rapido:
        return random.randint(20, 35)   # pos-mudanca: ~30s
    if modo_alerta:
        return random.randint(45, 65)   # zona de compra mudou: ~1min
    if 0 <= hora < 8:
        return random.randint(50, 70)   # madrugada: ~1min (mais frequente)
    elif 8 <= hora < 10 or 22 <= hora < 24:
        return random.randint(80, 110)  # transicao: ~1.5min
    else:
        return random.randint(110, 140) # horario comercial: ~2min

# ╔══════════════════════════════════════════════════════════════╗
# ║         🔗 API INTERNA TICKETMASTER                         ║
# ╚══════════════════════════════════════════════════════════════╝
def verificar_api_interna(show):
    """
    Tenta chamar o endpoint JSON interno do Ticketmaster.
    Mais rapido e confiavel que raspar HTML.
    Retorna (status, detalhes) ou None se nao conseguir.
    """
    # Extrai o slug do evento da URL
    slug = show["url"].rstrip("/").split("/")[-1]

    endpoints = [
        f"https://www.ticketmaster.com.br/api/v2/event/{slug}",
        f"https://www.ticketmaster.com.br/api/event/{slug}/availability",
        f"https://www.ticketmaster.com.br/api/v1/products?event={slug}",
    ]

    headers_api = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": show["url"],
        "X-Requested-With": "XMLHttpRequest",
    }

    for endpoint in endpoints:
        try:
            r = fazer_request(endpoint, timeout=15)
            if r.status_code == 200:
                try:
                    data     = r.json()
                    data_str = str(data).lower()
                    print(f"     API interna respondeu: {endpoint}")

                    # Analisa resposta JSON
                    disponivel = any(p in data_str for p in [
                        "available", "on_sale", "onsale", "buy", "active",
                        "disponivel", "venda", "comprar"
                    ])
                    esgotado = any(p in data_str for p in [
                        "sold_out", "soldout", "unavailable", "esgotado", "cancelled"
                    ])

                    if disponivel and not esgotado:
                        return "disponivel", {"sinais": ["API interna confirmou disponibilidade"], "setores": [], "precos": [], "tipos": []}
                    elif esgotado:
                        return "esgotado", []
                    else:
                        return "nao_disponivel", []
                except Exception:
                    pass  # resposta nao e JSON, ignora
        except Exception:
            pass

    return None, None  # API nao acessivel, usar HTML normal

# ╔══════════════════════════════════════════════════════════════╗
# ║                   📩 ENVIAR MENSAGEM                        ║
# ╚══════════════════════════════════════════════════════════════╝
def enviar_telegram(mensagem, tentativas_max=5):
    for tentativa in range(tentativas_max):
        try:
            url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}
            r       = requests.post(url, json=payload, timeout=15)
            resp    = r.json()
            if resp.get("ok"):
                print(f"  OK Telegram enviado! [{datetime.now().strftime('%H:%M:%S')}]")
                return True
            else:
                print(f"  AVISO Telegram rejeitou (tentativa {tentativa+1}): {resp.get('description','')}")
        except Exception as e:
            print(f"  ERRO Telegram (tentativa {tentativa+1}): {e}")
        if tentativa < tentativas_max - 1:
            time.sleep(10 * (tentativa + 1))
    print("  FALHA ao enviar Telegram apos todas tentativas.")
    return False

# ╔══════════════════════════════════════════════════════════════╗
# ║              🌐 VERIFICAR CONEXAO COM INTERNET              ║
# ╚══════════════════════════════════════════════════════════════╝
def tem_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def aguardar_internet():
    if not tem_internet():
        print("  Sem internet! Aguardando reconexao...")
        while not tem_internet():
            time.sleep(30)
        print("  Internet restaurada!")

# ╔══════════════════════════════════════════════════════════════╗
# ║            🔍 VERIFICAR DISPONIBILIDADE MAXIMA              ║
# ╚══════════════════════════════════════════════════════════════╝
def extrair_detalhes(html):
    """Extrai o maximo de informacao possivel do HTML da pagina."""
    html_lower = html.lower()
    detalhes = {}

    # ── Setores ──────────────────────────────────────────────
    palavras_setor = [
        "pista", "pista premium", "pista vip", "arena", "cadeira",
        "cadeira inferior", "cadeira superior", "camarote", "vip",
        "platinum", "superior", "inferior", "frente de palco",
        "lateral", "mezanino", "floor", "stage", "golden circle",
        "premium", "backstage", "arquibancada", "tribuna",
        "setor a", "setor b", "setor c", "setor d",
        "setor 1", "setor 2", "setor 3",
        "pista frontal", "pista lateral", "pista geral",
    ]
    setores = []
    for palavra in palavras_setor:
        if palavra in html_lower:
            setores.append(palavra.upper())
    detalhes["setores"] = list(dict.fromkeys(setores)) if setores else []

    # ── Precos ───────────────────────────────────────────────
    precos = re.findall(r'R\$\s*[\d.,]+', html)
    precos_unicos = list(dict.fromkeys(precos))[:8]
    detalhes["precos"] = precos_unicos

    # ── Quantidade / disponibilidade ─────────────────────────
    qtd = re.findall(r'(\d+)\s*(?:ingresso|ticket|disponivel|available)', html_lower)
    detalhes["quantidades"] = list(dict.fromkeys(qtd))[:5]

    # ── Palavras-chave que confirmam disponibilidade ──────────
    sinais_confirmados = []
    mapa_sinais = {
        "comprar ingresso": "Botao COMPRAR detectado",
        "add to cart": "Botao ADD TO CART detectado",
        "buy now": "Botao BUY NOW detectado",
        "select tickets": "Selecao de ingressos ativa",
        "seatmap": "Mapa de assentos carregado",
        "pricezone": "Zonas de preco detectadas",
        "offercode": "Codigo de oferta encontrado",
        "inventorytype": "Inventario de ingressos detectado",
        "addtocart": "Funcao carrinho detectada",
        "buybutton": "Botao de compra ativo",
        "ticketid": "ID de ingresso encontrado",
        "finalizar compra": "Finalizacao de compra disponivel",
        "selecione o setor": "Selecao de setor disponivel",
        "quantidade de ingressos": "Campo de quantidade ativo",
    }
    for chave, descricao in mapa_sinais.items():
        if chave in html_lower:
            sinais_confirmados.append(descricao)
    detalhes["sinais"] = sinais_confirmados

    # ── Tipo de ingresso ─────────────────────────────────────
    tipos = []
    for tipo in ["meia estudante", "meia-estudante", "estudante", "meia", "inteira", "half price", "full price", "student", "social"]:
        if tipo in html_lower:
            tipos.append(tipo.upper())
    detalhes["tipos"] = list(dict.fromkeys(tipos))

    # ── HTML bruto (usado pelo filtro de setor) ──────────────
    detalhes["_html_raw"] = html[:50000]  # primeiros 50kb sao suficientes

    return detalhes

# ╔══════════════════════════════════════════════════════════════╗
# ║         🤖 CONFIRMACAO INTELIGENTE COM GROQ                 ║
# ╚══════════════════════════════════════════════════════════════╝
def confirmar_com_groq(html_trecho, artista, data_show):
    """
    Envia um trecho do HTML para o Groq confirmar se realmente
    ha ingressos disponiveis para compra.
    Retorna True (confirmado), False (falso positivo) ou None (erro/groq indisponivel).
    """
    if not GROQ_API_KEY:
        return None  # Groq nao configurado, prossegue sem confirmar

    # Limita o trecho para nao estourar tokens
    trecho = html_trecho[:6000]

    prompt = (
        f"Voce e um analisador de paginas do Ticketmaster Brasil.\n"
        f"Artista: {artista} | Data do show: {data_show}\n\n"
        f"Analise o HTML/texto abaixo e responda SOMENTE com um JSON no formato:\n"
        f"{{\"disponivel\": true/false, \"motivo\": \"explicacao curta\"}}\n\n"
        f"Criterios para disponivel=true:\n"
        f"- Ha botao de compra ativo (comprar, buy, add to cart, etc)\n"
        f"- Ha selecao de setores ou ingressos\n"
        f"- Ha precos exibidos com opcao de compra\n"
        f"- Nao e apenas propaganda, pagina de espera ou 'em breve'\n\n"
        f"Criterios para disponivel=false:\n"
        f"- Pagina de espera, fila virtual, captcha\n"
        f"- Apenas 'em breve', 'coming soon', 'notify me'\n"
        f"- Esgotado, sold out\n"
        f"- Pagina generica sem opcao real de compra\n\n"
        f"HTML/texto:\n{trecho}"
    )

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0,
            },
            timeout=20,
        )

        if r.status_code != 200:
            print(f"     [Groq] Erro HTTP {r.status_code}")
            return None

        conteudo = r.json()["choices"][0]["message"]["content"].strip()
        # Remove possiveis backticks de markdown
        conteudo = conteudo.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(conteudo)
        disponivel = resultado.get("disponivel", False)
        motivo = resultado.get("motivo", "")
        print(f"     [Groq] disponivel={disponivel} | {motivo}")
        return disponivel

    except json.JSONDecodeError:
        print(f"     [Groq] Resposta nao e JSON valido: {conteudo[:100]}")
        return None
    except Exception as e:
        print(f"     [Groq] Erro: {type(e).__name__}: {e}")
        return None


def verificar_show(show):
    tentativas = 4
    extra_backoff = backoff_show(show["data"])
    if extra_backoff > 0:
        print(f"     Backoff de {extra_backoff}s por erros anteriores nesse show...")
        time.sleep(extra_backoff)

    # ── Tenta API interna primeiro (mais rapido) ──────────────
    status_api, det_api = verificar_api_interna(show)
    if status_api == "disponivel":
        print(f"     API interna: DISPONIVEL!")
        resetar_erro_show(show["data"])
        return "disponivel", det_api, False
    elif status_api == "esgotado":
        print(f"     API interna: esgotado.")
        resetar_erro_show(show["data"])
        return "esgotado", [], False

    # ── Fallback: raspagem de HTML ────────────────────────────
    for tentativa in range(tentativas):
        try:
            if tentativa > 0:
                espera = random.uniform(20, 40) * tentativa  # mais espaçado para evitar 403
                print(f"     Aguardando {espera:.0f}s antes da tentativa {tentativa+1}...")
                time.sleep(espera)

            aguardar_internet()

            # Tentativa 1 e 2: direto. Tentativa 3+: ScraperAPI
            usar_scraper = (tentativa >= 2) and bool(SCRAPERAPI_KEY)
            r          = fazer_request(show["url"], timeout=40, forcar_scraper=usar_scraper)
            html       = r.text
            html_lower = html.lower()

            # Mostra resposta e conteudo em caso de erro
            print(f"     HTTP: {r.status_code} | Tamanho: {len(html)} bytes", end="")
            if r.status_code != 200 and len(html) < 200:
                print(f" | Resposta: {html[:150]}", end="")

            # So atualiza o hash se a pagina foi carregada com sucesso
            if r.status_code in [200, 301, 302]:
                mudou_total, mudou_zona = pagina_mudou(show["data"], html)
                if mudou_zona:
                    print(" | *** ZONA DE COMPRA MUDOU! ***", end="")
                elif mudou_total:
                    print(" | * pagina mudou *", end="")
            else:
                mudou_total, mudou_zona = False, False
            print()

            if r.status_code in [401, 403]:
                print(f"     Bloqueado ({r.status_code}) - tentativa {tentativa+1}/{tentativas}")
                registrar_erro_show(show["data"])
                if tentativa == tentativas - 1:
                    print(f"     Todas as tentativas bloqueadas ({r.status_code}).")
                    return "nao_disponivel", [], False
                time.sleep(random.uniform(15, 30))
                continue
            if r.status_code == 429:
                print(f"     Rate limit (429) - aguardando 90s...")
                time.sleep(90)
                registrar_erro_show(show["data"])
                continue
            if r.status_code == 503:
                print(f"     Servico indisponivel (503) - aguardando 60s...")
                time.sleep(60)
                registrar_erro_show(show["data"])
                continue
            if r.status_code not in [200, 301, 302]:
                print(f"     Status inesperado: {r.status_code}")
                registrar_erro_show(show["data"])
                continue

            # Fila virtual / captcha
            sinais_fila = [
                "captcha", "waiting room", "sala de espera",
                "fila virtual", "queue", "you are in line",
                "voce esta na fila", "wait here", "virtual queue",
                "please wait", "checking your browser", "akamai",
            ]
            if any(p in html_lower for p in sinais_fila):
                print(f"     FILA/CAPTCHA detectado!")
                resetar_erro_show(show["data"])
                return "fila", [], mudou_zona

            # Disponivel — so palavras que indicam venda ABERTA de verdade
            palavras_disponivel = [
                # Acoes diretas de compra (PT)
                "comprar ingresso", "compre agora", "adicionar ao carrinho",
                "comprar agora", "ingressos disponiveis", "ingresso disponivel",
                "selecione o setor", "selecione a quantidade", "escolha seu ingresso",
                "finalizar compra", "ir para o carrinho", "ingressos a partir",
                "venda aberta", "venda disponivel", "em venda",
                # Acoes diretas de compra (EN)
                "buy ticket", "buy now", "add to cart", "get tickets",
                "select tickets", "book now", "available tickets", "tickets available",
                # Sinais fortes do Ticketmaster (JSON interno)
                '"available":true', '"status":"available"',
                '"onSale":true', '"isAvailable":true', '"inStock":true',
                "addtocart", "buybutton",
            ]

            # Esgotado
            palavras_esgotado = [
                "esgotado", "sold out", "indisponivel",
                "evento encerrado", "vendas encerradas", "fora de estoque",
                "out of stock", "no tickets available", "tickets unavailable",
                "ingresso esgotado", "setor esgotado", "todos os setores esgotados",
                '"soldOut":true', '"sold_out":true', '"status":"soldout"',
                '"status":"sold_out"', '"available":false',
            ]

            # Ainda nao abriu
            palavras_ainda_nao = [
                "em breve", "coming soon", "venda em breve",
                "inscreva-se para ser avisado", "notify me", "stay tuned",
                "em breve disponivel", "aguarde", "acompanhe",
                "venda nao iniciada", "pre-venda em breve",
            ]

            disponivel = any(p in html_lower for p in palavras_disponivel)
            esgotado   = any(p in html_lower for p in palavras_esgotado)
            ainda_nao  = any(p in html_lower for p in palavras_ainda_nao)

            resetar_erro_show(show["data"])

            if disponivel and not esgotado:
                detalhes = extrair_detalhes(html)
                # ── Confirmacao inteligente com Groq ──────────────
                print(f"     Sinais de disponibilidade detectados! Confirmando com Groq...")
                groq_ok = confirmar_com_groq(
                    detalhes.get("_html_raw", html[:6000]),
                    show["artista"],
                    show["data"],
                )
                if groq_ok is False:
                    # Groq disse que nao e real — falso positivo
                    print(f"     [Groq] FALSO POSITIVO descartado.")
                    resetar_erro_show(show["data"])
                    return "nao_disponivel", [], mudou_zona
                elif groq_ok is True:
                    print(f"     [Groq] CONFIRMADO! Disponivel de verdade!")
                else:
                    # Groq indisponivel — confia na logica de regex mesmo
                    print(f"     [Groq] Indisponivel, usando deteccao por regex.")
                return "disponivel", detalhes, mudou_zona
            elif esgotado and not ainda_nao:
                return "esgotado", [], mudou_zona
            elif ainda_nao:
                return "nao_abriu", [], mudou_zona
            else:
                return "nao_disponivel", [], mudou_zona

        except requests.exceptions.Timeout:
            print(f"     Timeout - tentativa {tentativa+1}/{tentativas}")
            registrar_erro_show(show["data"])
        except requests.exceptions.ConnectionError:
            print(f"     Erro de conexao - tentativa {tentativa+1}/{tentativas}")
            registrar_erro_show(show["data"])
            aguardar_internet()
        except Exception as e:
            print(f"     Erro inesperado: {type(e).__name__}: {e}")
            registrar_erro_show(show["data"])

    return "erro", [], False

# ╔══════════════════════════════════════════════════════════════╗
# ║                    🔁 LOOP PRINCIPAL                        ║
# ╚══════════════════════════════════════════════════════════════╝
def monitorar():
    hora_inicio        = datetime.now()
    ja_notificados     = set()
    rodada             = 1
    ultima_msg_12h     = hora_inicio
    total_verif        = 0
    erros_consecutivos = 0
    # Rastreia status anterior de cada show para detectar mudancas (ex: esgotado -> disponivel)
    status_anterior    = {}
    # Contador de verificacoes rapidas pos-mudanca
    rodadas_rapidas    = {}

    # ── MENSAGEM INICIAL ──────────────────────────────────────
    msg_inicio = (
        f"✅ BOT INICIADO — JA MONITORANDO!\n"
        f"🕐 {hora_inicio.strftime('%d/%m/%Y as %H:%M:%S')}\n\n"
        f"📋 SHOWS MONITORADOS:\n"
        f"🌹 The Rose — 21/06/2026 (Domingo)\n"
        f"   Avisa so se Pista Premium + Meia Estudante\n\n"
        f"💜 BTS World Tour Arirang\n"
        f"   28/10 (Quarta) · 30/10 (Sexta) · 31/10 (Sabado)\n"
        f"   Avisa qualquer ingresso disponivel\n\n"
        f"⚙️ COMO FUNCIONA:\n"
        f"🌙 Madrugada (0h-8h): verifica a cada ~1min\n"
        f"🌅 Transicao (8h-10h / 22h-24h): ~1,5min\n"
        f"☀️ Horario comercial (10h-22h): ~2min\n\n"
        f"🔕 Silencio total enquanto nao abrir.\n"
        f"📣 So te aviso quando for real:\n"
        f"   ingresso disponivel ou fila virtual ativa.\n\n"
        f"A cada 12h uma confirmacao de que estou rodando.\n"
        f"ARMY FIGHTING! 💜"
    )

    if SCRAPERAPI_KEY and SCRAPERAPI_KEY_RESERVA:
        scraper_status = "✅ ScraperAPI: 2 chaves configuradas (principal + reserva)"
    elif SCRAPERAPI_KEY:
        scraper_status = "✅ ScraperAPI: 1 chave configurada"
    else:
        scraper_status = "⚠️ ScraperAPI NAO configurada"
    msg_inicio = msg_inicio + f"\n\n{scraper_status}"
    print("Bot iniciado! Enviando mensagem inicial...")
    enviar_telegram(msg_inicio)

    while True:
        try:
            agora         = datetime.now()
            horas_rodando = (agora - hora_inicio).total_seconds() / 3600

            print(f"\n{'='*50}")
            print(f"Verificacao #{rodada} | {agora.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"{'='*50}")

            # ── Aviso a cada 12 horas ──────────────────────
            horas_desde_12h = (agora - ultima_msg_12h).total_seconds() / 3600
            if horas_desde_12h >= 12:
                # Monta status real de cada show
                linhas_status = []
                for s in SHOWS:
                    st = status_anterior.get(s["data"], "aguardando")
                    if st in ("nao_disponivel", "nao_abriu", "aguardando"):
                        emoji = "⏳"
                        st_txt = "Aguardando abrir"
                    elif st == "disponivel":
                        emoji = "✅"
                        st_txt = "DISPONIVEL"
                    elif st == "esgotado":
                        emoji = "❌"
                        st_txt = "Esgotado"
                    elif st == "fila":
                        emoji = "🟡"
                        st_txt = "Fila virtual"
                    else:
                        emoji = "⚠️"
                        st_txt = st

                    filtro_txt = " (Pista Premium + Meia)" if s.get("setor_filtro") else ""
                    linhas_status.append(f"{emoji} {s['artista']} - {s['dia']} {s['data']}{filtro_txt}: {st_txt}")

                status_txt = "\n".join(linhas_status)

                _, frase = random.choice(FRASES_BTS)

                enviar_telegram(
                    f"💜 BOT FUNCIONANDO NORMALMENTE!\n"
                    f"🕐 Rodando ha {horas_rodando:.0f}h\n"
                    f"🔍 Verificacoes feitas: {total_verif}\n\n"
                    f"📋 STATUS DOS SHOWS:\n"
                    f"{status_txt}\n\n"
                    f"⏱ Verificando a cada ~2 minutos, 24h por dia.\n"
                    f"So aviso quando tiver disponivel de verdade!\n\n"
                    f"{frase}"
                )
                ultima_msg_12h = agora
                print("Mensagem de 12h enviada!")

            # ── Verificacao dos shows ──────────────────────
            houve_mudanca_zona = False
            for show in SHOWS:
                data    = show["data"]
                artista = show.get("artista", "Show")
                filtro  = show.get("setor_filtro")  # ex: "pista premium" ou None
                print(f"\n[{data}] Verificando {artista} - {show['dia']}...")
                total_verif += 1

                if data in ja_notificados:
                    print(f"   Ja notificado, pulando.")
                    continue

                status, detalhes, mudou_zona = verificar_show(show)

                # ── Deteccao de mudanca na zona de compra ──
                if mudou_zona and status not in ("disponivel", "fila"):
                    houve_mudanca_zona = True
                    rodadas_rapidas[data] = 5
                    print(f"   ZONA DE COMPRA MUDOU! Entrando em modo rapido (silencioso)...")

                # ── Esgotado voltou (devolucao/cancelamento) ──
                if status_anterior.get(data) == "esgotado" and status == "disponivel":
                    enviar_telegram(
                        f"🔄 VOLTOU! {artista}\n"
                        f"📅 {show['dia']} - {data}\n\n"
                        f"Ingresso que estava esgotado voltou a ficar disponivel!\n"
                        f"Pode ser devolucao ou cancelamento.\n\n"
                        f"🔗 {show['url']}"
                    )

                status_anterior[data] = status

                if status == "disponivel":
                    erros_consecutivos = 0
                    det       = detalhes
                    setores   = det.get("setores", [])
                    tipos_raw = det.get("tipos", [])
                    html_raw  = det.get("_html_raw", "").lower()

                    # ── Filtro de setor (The Rose: Pista Premium) ────────
                    filtro_setor = show.get("setor_filtro")
                    if filtro_setor:
                        setor_ok = (
                            any(filtro_setor.lower() in s.lower() for s in setores) or
                            filtro_setor.lower() in html_raw
                        )
                        if not setor_ok:
                            print(f"   Disponivel mas '{filtro_setor}' nao detectado - aguardando.")
                            continue

                    # ── Filtro de tipo (The Rose: Meia Estudante) ────────
                    filtro_tipo = show.get("tipo_filtro")
                    if filtro_tipo:
                        tipo_ok = any(
                            tp.lower() in html_raw or any(tp.lower() in t.lower() for t in tipos_raw)
                            for tp in filtro_tipo
                        )
                        if not tipo_ok:
                            print(f"   Pista Premium ok mas meia/estudante nao detectada - aguardando.")
                            continue

                    # ── Monta textos ─────────────────────────────────────
                    setores_txt = "\n".join([f"  • {s}" for s in setores]) if setores else "  • Verificar no site"
                    precos_txt  = "  " + " | ".join(det.get("precos", [])) if det.get("precos") else "  Verificar no site"
                    tipos_txt   = "  " + " | ".join(tipos_raw) if tipos_raw else "  Verificar no site"

                    # ── Alerta BTS ───────────────────────────────────────
                    if artista == "BTS":
                        alerta = (
                            f"🚨 BTS - COMPRA ABERTA!\n"
                            f"💜 BTS WORLD TOUR - ARIRANG\n"
                            f"📅 {show['dia'].upper()} - {data}\n"
                            f"🕐 {agora.strftime('%d/%m %H:%M:%S')}\n\n"
                            f"🏟 SETORES:\n{setores_txt}\n\n"
                            f"💰 PRECOS:\n{precos_txt}\n\n"
                            f"🎟 TIPOS:\n{tipos_txt}\n\n"
                            f"🔗 {show['url']}\n\n"
                            f"⚡ CORRE! ARMY FIGHTING! 💜"
                        )

                    # ── Alerta The Rose ──────────────────────────────────
                    else:
                        meia_txt = ""
                        for tp in (filtro_tipo or []):
                            if tp.lower() in html_raw or any(tp.lower() in t.lower() for t in tipos_raw):
                                meia_txt = "\n⭐ MEIA ESTUDANTE DISPONIVEL!\n"
                                break

                        alerta = (
                            f"🚨 THE ROSE - PISTA PREMIUM ABRIU!\n"
                            f"🌹 THE ROSE - SAO PAULO\n"
                            f"📅 {show['dia'].upper()} - {data}\n"
                            f"🕐 {agora.strftime('%d/%m %H:%M:%S')}\n\n"
                            f"✅ PISTA PREMIUM DISPONIVEL!{meia_txt}\n"
                            f"🏟 SETORES:\n{setores_txt}\n\n"
                            f"💰 PRECOS:\n{precos_txt}\n\n"
                            f"🎟 TIPOS:\n{tipos_txt}\n\n"
                            f"🔗 {show['url']}\n\n"
                            f"⚡ CORRE!"
                        )

                    # ── Envia 3x com 5s de intervalo ────────────────────
                    for i in range(3):
                        enviar_telegram(alerta)
                        if i < 2:
                            time.sleep(5)

                    # Marca so ESSE dia — os outros continuam monitorados!
                    ja_notificados.add(data)
                    print(f"   DISPONIVEL! Alerta 3x enviado! Outros shows continuam monitorados.")

                    # ── Confirmacao em rajada: 5x nos proximos 2min ──────
                    print(f"   Iniciando confirmacao em rajada...")
                    for conf in range(5):
                        time.sleep(25)
                        st2, det2, _ = verificar_show(show)  # confirmacao usa ScraperAPI internamente se necessario
                        if st2 == "disponivel":
                            enviar_telegram(
                                f"✅ AINDA ABERTO! ({conf+1}/5)\n"
                                f"{artista} - {show['dia']} {data}\n"
                                f"🔗 {show['url']}"
                            )
                        else:
                            enviar_telegram(
                                f"⚠️ ({conf+1}/5) Status mudou para '{st2}'\n"
                                f"Pode ter esgotado rapido. Tenta mesmo assim!\n"
                                f"🔗 {show['url']}"
                            )
                            break

                elif status == "fila":
                    erros_consecutivos = 0
                    alerta_fila = (
                        f"🟡 FILA VIRTUAL ATIVA!\n"
                        f"{artista} - {show['dia']} - {data}\n"
                        f"🕐 {agora.strftime('%d/%m %H:%M:%S')}\n\n"
                        f"A venda pode estar abrindo agora.\n"
                        f"Entre na fila imediatamente!\n\n"
                        f"🔗 {show['url']}"
                    )
                    for i in range(3):
                        enviar_telegram(alerta_fila)
                        if i < 2:
                            time.sleep(5)
                    print(f"   FILA detectada! Alerta 3x enviado!")

                elif status == "esgotado":
                    erros_consecutivos = 0
                    print(f"   Esgotado - monitorando por se liberar algum...")

                elif status == "nao_abriu":
                    erros_consecutivos = 0
                    print(f"   Venda ainda nao abriu - aguardando...")

                elif status == "erro":
                    erros_consecutivos += 1
                    print(f"   Erro - consecutivos: {erros_consecutivos}")
                    if erros_consecutivos >= 10:
                        enviar_telegram(
                            f"⚠️ {erros_consecutivos} erros seguidos\n"
                            f"Ticketmaster pode estar bloqueando.\n"
                            f"Continuando tentativas...\n"
                            f"🕐 {agora.strftime('%d/%m %H:%M')}"
                        )
                        erros_consecutivos = 0
                else:
                    erros_consecutivos = 0
                    print(f"   Ainda nao disponivel.")

                time.sleep(random.uniform(4, 9))

            rodada += 1

            # ── Intervalo dinamico por horario e estado ────
            # Verifica se algum show ainda esta em modo rapido
            em_modo_rapido = any(
                rodadas_rapidas.get(s["data"], 0) > 0
                for s in SHOWS if s["data"] not in ja_notificados
            )
            # Decrementa contadores de rodadas rapidas
            for data in list(rodadas_rapidas.keys()):
                if rodadas_rapidas[data] > 0:
                    rodadas_rapidas[data] -= 1

            if em_modo_rapido:
                espera = intervalo_por_horario(modo_rapido=True)
                print(f"\nModo rapido! Proxima verificacao em {espera}s...")
            elif houve_mudanca_zona:
                espera = intervalo_por_horario(modo_alerta=True)
                print(f"\nModo alerta! Proxima verificacao em {espera}s...")
            else:
                espera = intervalo_por_horario()
                hora_atual = datetime.now().hour
                if 0 <= hora_atual < 8:
                    modo_str = "madrugada (frequente)"
                elif 8 <= hora_atual < 10 or 22 <= hora_atual < 24:
                    modo_str = "transicao"
                else:
                    modo_str = "horario comercial"
                print(f"\nModo {modo_str}. Proxima verificacao em {espera}s...")
            time.sleep(espera)

        except KeyboardInterrupt:
            print("\nBot encerrado manualmente.")
            enviar_telegram("Bot encerrado manualmente. Ate logo!")
            raise
        except Exception as e:
            erros_consecutivos += 1
            print(f"\nErro no loop: {type(e).__name__}: {str(e)[:150]}")
            print(traceback.format_exc())
            try:
                enviar_telegram(
                    f"Erro interno detectado!\n"
                    f"Tipo: {type(e).__name__}\n"
                    f"Recuperando automaticamente...\n"
                    f"Horario: {datetime.now().strftime('%d/%m %H:%M')}\n"
                    f"Bot continua rodando!"
                )
            except Exception:
                pass
            time.sleep(30)

# ╔══════════════════════════════════════════════════════════════╗
# ║                    PONTO DE ENTRADA                         ║
# ╚══════════════════════════════════════════════════════════════╝
def main():
    print("=" * 50)
    print("  BOT BTS ARMY - INICIANDO")
    print("=" * 50)
    reinicializacoes = 0
    while True:
        try:
            monitorar()
        except KeyboardInterrupt:
            print("\nEncerrando bot. Tchau!")
            break
        except Exception as e:
            reinicializacoes += 1
            print(f"\nReinicializacao #{reinicializacoes} | Erro: {e}")
            print("Reiniciando em 20 segundos...")
            try:
                enviar_telegram(
                    f"⚠️ Bot reiniciado pelo Railway!\n"
                    f"Reinicializacao #{reinicializacoes}\n"
                    f"Erro: {str(e)[:80]}\n"
                    f"Voltando em 20 segundos...\n"
                    f"Nunca vou parar por voce!"
                )
            except Exception:
                pass
            time.sleep(20)

if __name__ == "__main__":
    main()
