import streamlit as st
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime
from io import BytesIO
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Cria um placeholder para o log no Streamlit
log_output = st.empty()
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Lista para armazenar os logs
logs = []

# Função para exibir logs no Streamlit, agora acumulando os logs na lista e exibindo abaixo
def atualizar_log(message, log_area):
    logs.append(message)  # Adiciona cada log à lista
    log_area.text_area("Log de Execução", value="\n".join(logs), height=550)  # Atualiza a área de texto

# Função para iniciar o navegador com configuração de log silenciosa
def iniciar_navegador_silencioso():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Executa o navegador no modo headless
    options.add_argument("--no-sandbox")  # Necessário para ambientes Linux com permissões restritas
    options.add_argument("--disable-dev-shm-usage")  # Reduz problemas de memória
    options.add_argument('--disable-gpu')  # Desabilita o uso de GPU
    options.add_argument('--disable-extensions')  # Desabilita extensões
    options.add_argument('--disable-infobars')  # Desabilita a barra de informações
    options.add_argument('--disable-popup-blocking')  # Desabilita o bloqueio de pop-ups
    options.add_argument('--blink-settings=imagesEnabled=false')  # Desabilita imagens para reduzir consumo de banda
    
    # Instala e usa automaticamente o ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Exemplo de execução
log_area = st.empty()  # Cria uma área para o log

# Atualiza o log durante o processo
print("Iniciando o navegador no modo headless...", log_area)

try:
    driver = iniciar_navegador_silencioso()
    print("Navegador iniciado com sucesso!", log_area)

    # Exemplo de navegação
    driver.get('https://www.google.com')
    print(f"Página acessada: {driver.title}", log_area)

except Exception as e:
    print(f"Erro ao iniciar o navegador: {str(e)}", log_area)

finally:
    driver.quit()
    print("Navegador fechado.", log_area)

# Função para registrar o resultado da busca
resultado_final = []
total_registros = 0

def registrar_resultado(sucesso, site, quantidade=0):
    global total_registros
    status = 'SUCESSO' if sucesso else 'FALHA'
    resultado_final.append(f"{site}: {status} - {quantidade} registros encontrados" if sucesso else f"{site}: {status}")
    if sucesso:
        total_registros += quantidade

# Funções de busca para cada site
def search_dados_gov(termo_busca_pt, log_area):
    site = "dados.gov.br"
    atualizar_log(f"Iniciando busca em {site}", log_area)
    
    nav = iniciar_navegador_silencioso()
    nav.get('https://dados.gov.br/home')

    try:
        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="search2"]'))
        )
        search_input.send_keys(termo_busca_pt)
        search_input.send_keys(Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="conjunto-dados"]/div[1]//div[@class="card w-100 ratio ratio-1x1 relative hoverable-card border-blue-cool-vivid-30"]'))
        )

        cards = nav.find_elements(By.XPATH, '//*[@id="conjunto-dados"]/div[1]//div[@class="card w-100 ratio ratio-1x1 relative hoverable-card border-blue-cool-vivid-30"]')
        dados = [(site, card.find_element(By.TAG_NAME, 'a').text, card.find_element(By.TAG_NAME, 'a').get_attribute('href')) for card in cards[:10]]
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar em {site}")
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return dados

def search_ipea(termo_busca_pt, log_area):
    site = "ipea.gov.br"
    atualizar_log(f"Iniciando busca em {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://www.ipea.gov.br/portal/')

    try:
        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="mod-finder-searchword156"]'))
        )
        search_input.send_keys(termo_busca_pt + Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'search-resultsbusca_title'))
        )

        resultados = nav.find_elements(By.CLASS_NAME, 'search-resultsbusca_title')
        dados = [(site, resultado.find_element(By.XPATH, './/h4/a').text, resultado.find_element(By.XPATH, './/h4/a').get_attribute('href')) for resultado in resultados[:10]]
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar em {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return dados

def search_biblioteca_digital_fgv(termo_busca_pt, log_area):
    site = "sistema.bibliotecas.fgv.br"
    atualizar_log(f"Iniciando busca na {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://sistema.bibliotecas.fgv.br/search/node')

    try:
        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="edit-keys"]'))
        )
        search_input.send_keys(termo_busca_pt)
        search_input.send_keys(Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ol.search-results.node-results li.search-result'))
        )

        search_results = nav.find_elements(By.CSS_SELECTOR, 'ol.search-results.node-results li.search-result')
        dados = [(site, result.find_element(By.CLASS_NAME, 'title').text.strip(), result.find_element(By.CLASS_NAME, 'title').find_element(By.TAG_NAME, 'a').get_attribute('href')) for result in search_results[:10]]
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar na {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca na {site} concluída", log_area)
    return dados

def search_scholar_google(termo_busca_pt, log_area):
    site = "scholar.google.com.br"
    atualizar_log(f"Iniciando busca no {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://scholar.google.com.br/schhp?hl=pt-BR')

    try:
        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="gs_hdr_tsi"]'))
        )
        search_input.send_keys(termo_busca_pt)
        search_input.send_keys(Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'gs_r.gs_or.gs_scl'))
        )

        div_results = nav.find_element(By.ID, 'gs_res_ccl')
        posts = div_results.find_elements(By.CLASS_NAME, 'gs_r.gs_or.gs_scl')
        dados = []
        for post in posts[:10]:
            try:
                title_element = post.find_element(By.CLASS_NAME, 'gs_rt')
                title = title_element.text
                link = post.find_element(By.TAG_NAME, 'a').get_attribute('href')
                dados.append((site, title, link))
            except NoSuchElementException:
                continue
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar no {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca no {site} concluída", log_area)
    return dados

def search_sidra_ibge(termo_busca_pt, log_area):
    site = "sidra.ibge.gov.br"
    atualizar_log(f"Iniciando busca no {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://sidra.ibge.gov.br/home/ipca/brasil')

    try:
        search_icon = WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sidra-menu-collapse"]/ul/li[8]/a/i'))
        )
        search_icon.click()

        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="sidra-pesquisa-lg"]/form/div/input'))
        )
        search_input.send_keys(termo_busca_pt)
        search_input.send_keys(Keys.RETURN)

        WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.ID, 'lista-busca'))
        )

        tabela = nav.find_element(By.ID, 'lista-busca')
        linhas = tabela.find_elements(By.TAG_NAME, 'tr')
        dados = []
        for i in range(min(len(linhas), 10)):
            celulas = linhas[i].find_elements(By.TAG_NAME, 'td')
            if len(celulas) >= 2:
                titulo_element = celulas[1].find_element(By.TAG_NAME, 'a')
                dados.append((site, titulo_element.text, titulo_element.get_attribute('href')))
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar no {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca no {site} concluída", log_area)
    return dados

def search_statista(termo_busca_eng, log_area):
    site = "statista.com"
    atualizar_log(f"Iniciando busca em {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://www.statista.com/')

    try:
        WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        ).click()

        campo_busca = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
        )
        campo_busca.send_keys(termo_busca_eng)
        campo_busca.submit()

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-gtm-contenttype="statistic"]'))
        )

        divs_conteudo = nav.find_elements(By.CSS_SELECTOR, 'div[data-gtm-contenttype="statistic"]')
        resultados = [(site, div.find_element(By.CSS_SELECTOR, 'div.itemContent__text').text.strip(), div.find_element(By.CSS_SELECTOR, 'a[data-gtm]').get_attribute('href')) for div in divs_conteudo[:10]]
        registrar_resultado(True, site, len(resultados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar em {site}", log_area)
        registrar_resultado(False, site)
        resultados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return resultados

def search_gartner(termo_busca_eng, log_area):
    site = "gartner.com.br"
    atualizar_log(f"Iniciando busca em {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://www.gartner.com.br/pt-br')

    try:
        WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="search-button-util-nav"]/span'))
        ).click()

        search_input_1 = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="searchString"]'))
        )
        search_input_1.send_keys(termo_busca_eng)
        search_input_1.send_keys(Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'search-item'))
        )

        div_element = nav.find_element(By.CLASS_NAME, 'search-result')
        search_items = div_element.find_elements(By.CLASS_NAME, 'search-item')

        dados = [(site, item.find_element(By.CLASS_NAME, 'result-heading').text, item.find_element(By.CLASS_NAME, 'result-heading').get_attribute('href')) for item in search_items[:10]]
        registrar_resultado(True, site, len(dados))

    except (TimeoutException, NoSuchElementException):
        atualizar_log(f"Timeout ou elemento não encontrado em {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return dados

def search_nielsen(termo_busca_pt, log_area):
    site = "nielsen.com"
    atualizar_log(f"Iniciando busca em {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://www.nielsen.com/pt/about-us/locations/brazil/')

    try:
        WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[9]/header/nav/nav[2]/a[1]'))
        ).click()

        search_input_1 = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="nav-search"]'))
        )
        search_input_1.send_keys(termo_busca_pt)
        search_input_1.send_keys(Keys.RETURN)

        WebDriverWait(nav, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.wp-block-query .wp-block-post'))
        )

        post_items = nav.find_elements(By.CSS_SELECTOR, '.wp-block-query .wp-block-post')
        dados = [(site, post_item.find_element(By.CLASS_NAME, 'entry-title').text, post_item.find_element(By.CLASS_NAME, 'entry-title').find_element(By.TAG_NAME, 'a').get_attribute('href')) for post_item in post_items[:10]]
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar em {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return dados

def search_harvard_business_review(termo_busca_eng, log_area):
    site = "hbr.org"
    atualizar_log(f"Iniciando busca em {site}", log_area)

    nav = iniciar_navegador_silencioso()
    nav.get('https://hbr.org/search?search_type=&term=&term=')

    try:
        search_input = WebDriverWait(nav, 10).until(
            EC.presence_of_element_located((By.ID, 'search'))
        )
        search_input.send_keys(termo_busca_eng + Keys.RETURN)

        WebDriverWait(nav, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.content-area--result.column h3 a'))
        )

        results = nav.find_elements(By.CSS_SELECTOR, 'div.content-area--result.column h3 a')
        dados = [(site, result.text, result.get_attribute('href')) for result in results[:10]]
        registrar_resultado(True, site, len(dados))

    except TimeoutException:
        atualizar_log(f"Timeout ao buscar em {site}", log_area)
        registrar_resultado(False, site)
        dados = []

    nav.quit()
    atualizar_log(f"Busca em {site} concluída", log_area)
    return dados

def combine_scripts(termo_busca_pt, termo_busca_eng, log_area):
    dados = []
    dados.extend(search_dados_gov(termo_busca_pt, log_area))
    #dados.extend(search_ipea(termo_busca_pt, log_area))
    #dados.extend(search_biblioteca_digital_fgv(termo_busca_pt, log_area))
    #dados.extend(search_scholar_google(termo_busca_pt, log_area))
    #dados.extend(search_sidra_ibge(termo_busca_pt, log_area))
    #dados.extend(search_statista(termo_busca_eng, log_area))
    #dados.extend(search_gartner(termo_busca_eng, log_area))
    #dados.extend(search_nielsen(termo_busca_pt, log_area))
    #dados.extend(search_harvard_business_review(termo_busca_eng, log_area))

    atualizar_log("Coleta de dados concluída. Gerando DataFrame e salvando em CSV", log_area)

   # Gerando o DataFrame
    df = pd.DataFrame(dados, columns=['Website', 'Title', 'Link'])

    # Adicionando data e hora ao nome do arquivo
    timestamp = datetime.now().strftime("%d%m%Y_%H%M")
    filename = f'Resultados_{timestamp}.xlsx'

    # Salvando o Excel em memória em vez de salvar no disco
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()  # Obtém o conteúdo do Excel gerado

    atualizar_log(f"Arquivo Excel '{filename}' gerado com sucesso", log_area)
    
    return processed_data, filename

# Streamlit App
st.title("Web Scrapper - APEX")

# Inputs do usuário
termo_busca_pt = st.text_input("Digite o termo de busca em português:")
termo_busca_eng = st.text_input("Digite o termo de busca em inglês:")

# Botão para iniciar a busca
if st.button("Iniciar busca"):
    if termo_busca_pt and termo_busca_eng:
        st.write("Buscando dados...")
        log_area = st.empty()  # Placeholder para o log
        atualizar_log("Iniciando coleta de dados de todas as fontes", log_area)  # Primeira mensagem
        excel_data, filename = combine_scripts(termo_busca_pt, termo_busca_eng, log_area)  # Passe log_area
        
        # Adicionar botão para download do Excel
        st.download_button(
            label="Baixar resultados em Excel",
            data=excel_data,
            file_name=filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.warning("Por favor, preencha ambos os termos de busca.")