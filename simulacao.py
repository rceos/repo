# Importações necessárias para o projeto de simulação de cartão
import streamlit as st
import pandas as pd
import json
import io

# Configuração da página: Layout amplo e título identificador
st.set_page_config(layout="wide", page_title="Simulador de Cartão - EOS")

# Carregamento seguro de credenciais de usuário
# Tratamento flexível para nomes com espaços
USERS = {k.replace('_', ' '): v for k, v in st.secrets["users"].items()}

# Mapeamento de arquivos de taxas por máquina e bandeira
# Estrutura permite fácil manutenção e expansão
csv_files = {
    "Pag Seguro": {
        "Visa": "dataset/Maquina 1 - Visa.CSV",
        "Master": "dataset/Maquina 1 - Master.CSV",
        "Diners": "dataset/Maquina 1 - Diners.CSV",
        "Demais": "dataset/Maquina 1 - Demais.CSV",
        "Link": "dataset/Maquina 1 - Link.CSV",
    },
    "Infinity": {
        "Visa": "dataset/Maquina 2 - Visa.CSV",
        "Master": "dataset/Maquina 2 - Master.CSV",
        "Demais": "dataset/Maquina 2 - Demais.CSV",
        "Link": "dataset/Maquina 2 - Link.CSV",
    }
}

# Função central de carregamento de taxas
# Implementa tratamento robusto de erros e padronização de dados
def carregar_taxas():
    # Dicionário para armazenar taxas processadas
    taxas_carregadas = {
        "Pag Seguro": {},
        "Infinity": {}
    }
    has_error = False
    
    # Iteração dinâmica sobre máquinas e bandeiras
    for machine, bandeiras in csv_files.items():
        for bandeira, file_path in bandeiras.items():
            try:
                # Carregamento e processamento do CSV
                df = pd.read_csv(file_path, delimiter=';', encoding='latin1')
                df.columns = ['Parcelas', 'Taxa']
                df['Parcelas'] = df['Parcelas'].astype(int)
                df['Taxa'] = df['Taxa'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                taxas_carregadas[machine][bandeira] = df.set_index('Parcelas')['Taxa'].to_dict()
            except FileNotFoundError:
                # Log de erro para arquivo não encontrado
                st.error(f"Erro: Arquivo '{file_path}' não encontrado. Verifique se os arquivos CSV estão na mesma pasta do script.")
                has_error = True
            except Exception as e:
                # Captura de erros genéricos durante processamento
                st.error(f"Erro ao carregar o arquivo '{file_path}': {e}")
                has_error = True
    
    return taxas_carregadas if not has_error else None

# Carregamento de taxas otimizado
# Armazenamento em session_state para evitar reprocessamento
if 'loaded_rates' not in st.session_state:
    st.session_state.loaded_rates = carregar_taxas()

# Validação crítica de carregamento de taxas
if st.session_state.loaded_rates is None:
    st.warning("Não foi possível carregar todas as taxas. Corrija os erros de arquivo para continuar.")
    st.stop()

# Referência global de taxas para uso na aplicação
taxas = st.session_state.loaded_rates

# Função de login: Implementação de autenticação básica
def login_page():
    # Interface centralizada de autenticação
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
	
    st.markdown("<p style='text-align: center;'>Por favor, faça login para acessar o simulador.</p>", unsafe_allow_html=True)

    login_col_left, login_col_center, login_col_right = st.columns([1, 1, 1])
    with login_col_center:
	    # Formulário de login com validação
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
			# Lógica de autenticação
            if submit_button:
                if username in USERS and USERS[username] == password:
					# Gerenciamento de sessão
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Bem-vindo(a), {username}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

# Função principal do simulador
# Centraliza a lógica de negócio e renderização da interface
def main_simulator_app():
    # Injeção de estilos customizados via CSS
    # Objetivo: melhorar experiência visual e usabilidade
    st.markdown("""
        <style>
		/* Estilos de componentes específicos */
        /* Foco em legibilidade e consistência visual */
            /* ESTILO PARA O LABEL DO st.metric */
            div[data-testid="stMetricLabel"] p {
                font-size: 1.1rem;
                font-weight: bold;
                color: #555555; /* cor cinza */
            }

            /* ESTILO PARA O VALOR DO st.metric */
            div[data-testid="stMetricValue"] {
                font-size: 1.5rem;
                font-weight: bolder;
                /*color: #FFFFFF; *//* Ou a cor que desejar para os valores */
            }


            /* --- CENTRALIZAR st.metric DENTRO DAS COLUNAS --- */
            /* Encontra o contêiner direto do st.metric e aplica flexbox */
            div[data-testid="stMetric"] {
                display: flex;
                flex-direction: column; /* Organiza label e value em coluna */
                align-items: center;    /* Centraliza horizontalmente */
                text-align: center;     /* Centraliza o texto dentro do metric */
                width: 100%;            /* Garante que o metric ocupe a largura total para centralizar */
            }
            /* Garante que o texto do label e do valor também sejam centralizados */
            div[data-testid="stMetric"] label p, div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                width: 100%; /* Ocupa a largura total para centralização */
}
                
            /* --- FORMATAÇÃO DO BOTÃO 'Simular' --- */
            div[data-testid="stFormSubmitButton"] > button {
                background-color: #FF8C00; /* Laranja escuro */
                color: #FFFFFF; /* Cor do texto do botão */
                border: none; /* Remove a borda */
                font-weight: bold; /* Texto do botão em negrito */
                padding: 10px 20px; /* Ajusta o padding para dar mais "corpo" ao botão */
                border-radius: 5px; /* Bordas levemente arredondadas */
                cursor: pointer; /* Indica que é clicável */
                transition: background-color 0.3s ease; /* Transição suave na cor de fundo */
                width: 100%; /* Faz o botão ocupar 100% da largura da sua coluna pai */
            }

            /* ESTILO AO PASSAR O MOUSE POR CIMA DO BOTÃO */
            div[data-testid="stFormSubmitButton"] > button:hover {
                background-color: #FFA500; /* Laranja mais claro no hover */
                font-weight: bold;
                color: #FFFFFF; /* Garante branco no hover */
            }
                
            /* Estilo ao CLICAR (ativo) ou FOCAR no botão */
            div[data-testid="stFormSubmitButton"] > button:active,
            div[data-testid="stFormSubmitButton"] > button:focus {
                color: #FFFFFF !important; /* Força o branco no clique/foco */
                outline: none; /* Remove a borda de foco padrão do navegador */
                box-shadow: none; /* Remove a sombra de foco padrão do Streamlit/navegador */
            }

            /* Centralizar o botão dentro de sua coluna */
            div[data-testid="stFormSubmitButton"] {
                display: flex;
                justify-content: center; /* Centraliza horizontalmente */
                width: 100%; /* Garante que a div pai ocupa toda a largura disponível para centralizar */
            }

            /* Ajuste para o texto dentro do botão, caso Streamlit adicione wrappers */
            div[data-testid="stFormSubmitButton"] > button > div {
                display: flex;
                justify-content: center;
                width: 100%;
            }
        </style>
        """, unsafe_allow_html=True)

    # Cabeçalho e descrição da aplicação
    st.markdown("<h2 style='text-align: center;'>Simulador de Cartão</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Compare as condições de parcelamento entre as maquininhas.</p>", unsafe_allow_html=True)
	
    # Sidebar: Gerenciamento de sessão e identificação do usuário
    st.sidebar.header(f"Bem-vindo(a), {st.session_state.username}!")
    st.sidebar.button("Sair", on_click=logout)

    col_left_spacer, col_center_inputs, col_right_spacer = st.columns([1, 1.2, 1])

    # Construção do formulário de entrada
    # Layout responsivo com colunas para centralização
    with col_center_inputs:
        # Input de valor: Tratamento robusto de entrada
        raw_amount = st.text_input(
            "💰 **Valor da Venda (R$)**",
            value="",
            placeholder="Digite um valor (ex: 5.000,00 ou 5000)",
            key="amount_input_text"
        )

        # Validação e formatação do valor de entrada
        amount = None
        if raw_amount:
            try:
                # Conversão flexível de formato monetário
                amount = float(raw_amount.replace(',', '.'))
                # Validações de negócio
                if amount < 0.01:
                    st.error("O valor da venda deve ser maior que R$ 0,00.")
                    amount = None
                else:
                    # Adiciona a exibição do valor formatado logo abaixo da entrada
                    st.info(f"Valor digitado: **R$ {amount:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            except ValueError:
                # Tratamento de erro para entrada inválida
                st.error("Por favor, digite um valor numérico válido para a venda.")
                amount = None

        # Seleção dinâmica de bandeiras disponíveis
        bandeiras_disponiveis = sorted(list(set(list(taxas.get('Pag Seguro', {}).keys()) + list(taxas.get('Infinity', {}).keys()))))
		
		# Função auxiliar de cálculo
		# Encapsula lógica de processamento de taxas por máquina
        display_bandeiras = ['-- Selecione uma bandeira --'] + bandeiras_disponiveis

        bandeira_selecionada = st.selectbox("💳 **Bandeira do Cartão**", display_bandeiras, key="bandeira_selector")

        if bandeira_selecionada == '-- Selecione uma bandeira --':
            bandeira = "N/A"
        else:
            bandeira = bandeira_selecionada

        if bandeira != "N/A":
            m1_parcelas = list(taxas.get('Pag Seguro', {}).get(bandeira, {}).keys())
            m2_parcelas = list(taxas.get('Infinity', {}).get(bandeira, {}).keys())
            parcelas_disponiveis = sorted(list(set(m1_parcelas + m2_parcelas)))
        else:
            parcelas_disponiveis = []

        if not parcelas_disponiveis:
            parcelas = st.selectbox("🔢 **Número de Parcelas**", ["N/A"], disabled=True, key="installments_selector_disabled")
        else:
            default_parcela_value = 1 if 1 in parcelas_disponiveis else parcelas_disponiveis[0]
            parcelas = st.selectbox(
                "🔢 **Número de Parcelas**",
                parcelas_disponiveis,
                index=parcelas_disponiveis.index(default_parcela_value),
                key="installments_selector_enabled"
            )
        
        st.session_state.selected_amount = amount
        st.session_state.selected_bandeira = bandeira
        st.session_state.selected_parcelas = parcelas

        with st.form("simulation_submit_form"):
            submit_simulation = st.form_submit_button("Simular") # O CSS acima irá estilizar este botão

    def calculate_machine_data(valor_venda, bandeira_valor, qtd_parcela, machine_rates_data):
        # Validações iniciais de entrada
        if bandeira_valor == "N/A" or qtd_parcela == "N/A" or valor_venda is None or valor_venda <= 0:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        # Recuperação segura de taxas
        rates_for_bandeira = machine_rates_data.get(bandeira_valor, {})
		# Verificação de existência de taxa para parcelamento
        if not rates_for_bandeira or qtd_parcela not in rates_for_bandeira:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        # Cálculos financeiros
        taxa = rates_for_bandeira[qtd_parcela]

        valor_final_venda = valor_venda * (1 + (taxa / 100))
        valor_liquido_venda = valor_venda # O valor líquido que o vendedor recebe é o valor original
        encargos_da_transacao = valor_final_venda - valor_venda
        parcela_cliente = valor_final_venda / qtd_parcela

        return valor_final_venda, parcela_cliente, valor_liquido_venda, encargos_da_transacao, taxa

    # Lógica de submissão e processamento da simulação
    if submit_simulation:
        # Recuperação de dados da sessão
        final_amount = st.session_state.selected_amount
        final_bandeira = st.session_state.selected_bandeira
        parcelas_finais = st.session_state.selected_parcelas

        # Validação final antes de processamento
        if final_amount is not None and final_amount > 0 and final_bandeira != "N/A" and parcelas_finais != "N/A":
            st.markdown("<h4 style='text-align: center;'>Resultados da Simulação</h4>", unsafe_allow_html=True)
            
			
            col1_results, col2_results = st.columns(2) 
			# Cálculo para diferentes máquinas de cartão
            m1_total_cliente, m1_parcela_cliente, m1_valor_liquido, m1_transaction_fees, m1_tax_rate = \
                calculate_machine_data(final_amount, final_bandeira, parcelas_finais, taxas.get('Pag Seguro', {}))

            with col1_results:
                st.markdown("<h3 style='text-align: center; color: #F6DF44; font-weight: bolder;'>PagBank</h3>", unsafe_allow_html=True)
                st.markdown("---")
                if m1_total_cliente != "N/A":
                    st.metric(label="Valor Recebido (EOS)", value=f"R$ {m1_valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m1_total_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m1_parcela_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Encargos (Cliente)", value=f"R$ {m1_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    # st.metric(label="Taxa Aplicada", value=f"{m1_tax_rate:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    st.warning("Pag Seguro: Dados não disponíveis para esta bandeira/parcelamento.")

            m2_total_cliente, m2_parcela_cliente, m2_valor_liquido, m2_transaction_fees, m2_tax_rate = \
                calculate_machine_data(final_amount, final_bandeira, parcelas_finais, taxas.get('Infinity', {}))

            with col2_results:
                st.markdown("<h3 style='text-align: center; color: #17EC2A; font-weight: bolder;'>InfinitePay</h3>", unsafe_allow_html=True)
                st.markdown("---")
                if m2_total_cliente != "N/A":
                    st.metric(label="Valor Recebido (EOS)", value=f"R$ {m2_valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m2_total_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m2_parcela_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Encargos (Cliente)", value=f"R$ {m2_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    # st.metric(label="Taxa Aplicada", value=f"{m2_tax_rate:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    st.warning("Infinity: Dados não disponíveis para esta bandeira/parcelamento.")
        else:
            st.warning("Por favor, preencha todos os campos corretamente (Valor, Bandeira e Parcelas) antes de simular.")
    else:
        st.info("Preencha os dados acima e clique em 'Simular' para ver os resultados.")

    st.markdown("---")
    st.markdown("Desenvolvido com Streamlit.")

# Função de logout: Gerenciamento seguro de sessão
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None

# Controlador de fluxo de autenticação
# Determina state da aplicação baseado em autenticação		  
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Renderização condicional	
if st.session_state.logged_in:
    main_simulator_app()
else:
    login_page()