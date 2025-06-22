import streamlit as st
import pandas as pd
import json
import io

# --- REMOVIDO: INJEÇÃO GLOBAL DE CSS PARA OCULTAR BOTÕES DE SPINNER (não é mais necessário com st.text_input) ---

st.set_page_config(layout="wide", page_title="Simulador de Cartão - Login")

# --- 1. Credenciais de Usuário (Carregadas de st.secrets) ---
# Access secrets.toml via st.secrets
# USERS = st.secrets["users"].to_dict() # This converts the section to a dictionary
# If you have keys with spaces in secrets.toml (e.g., "João Paulo"), you might need to iterate
USERS = {k.replace('_', ' '): v for k, v in st.secrets["users"].items()}


# --- 2. Função de Carregamento das Taxas (Mantida) ---
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
    }
}

def load_rates():
    all_loaded_rates = {
        "Pag Seguro": {},
        "Infinity": {}
    }
    has_error = False
    for machine, brands in csv_files.items():
        for brand, file_path in brands.items():
            try:
                df = pd.read_csv(file_path, delimiter=';', encoding='latin1')
                df.columns = ['Parcelas', 'Taxa']
                df['Parcelas'] = df['Parcelas'].astype(int)
                df['Taxa'] = df['Taxa'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                all_loaded_rates[machine][brand] = df.set_index('Parcelas')['Taxa'].to_dict()
            except FileNotFoundError:
                st.error(f"Erro: Arquivo '{file_path}' não encontrado. Verifique se os arquivos CSV estão na mesma pasta do script.")
                has_error = True
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo '{file_path}': {e}")
                has_error = True
    return all_loaded_rates if not has_error else None

# Carrega as taxas uma vez e armazena no session_state para evitar recarregar a cada interação
if 'loaded_rates' not in st.session_state:
    st.session_state.loaded_rates = load_rates()

if st.session_state.loaded_rates is None:
    st.warning("Não foi possível carregar todas as taxas. Corrija os erros de arquivo para continuar.")
    st.stop()

rates = st.session_state.loaded_rates

# --- 3. Função da Página de Login ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Por favor, faça login para acessar o simulador.</p>", unsafe_allow_html=True)

    login_col_left, login_col_center, login_col_right = st.columns([1, 1, 1])
    with login_col_center:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")

            if submit_button:
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Bem-vindo(a), {username}!")
                else:
                    st.error("Usuário ou senha incorretos.")

# --- 4. Função Principal da Aplicação (Simulador) ---
def main_simulator_app():
    # --- CSS PARA FORMATAR st.metric e Botão ---
    st.markdown("""
        <style>
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

    st.markdown("<h2 style='text-align: center;'>Simulador de Cartão</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Compare as condições de parcelamento entre as maquininhas.</p>", unsafe_allow_html=True)

    st.sidebar.header(f"Bem-vindo(a), {st.session_state.username}!")
    st.sidebar.button("Sair", on_click=logout)

    col_left_spacer, col_center_inputs, col_right_spacer = st.columns([1, 1.2, 1])

    with col_center_inputs:
        raw_amount = st.text_input(
            "💰 **Valor da Venda (R$)**",
            value="",
            placeholder="Digite um valor (ex: 5.000,00 ou 5000)",
            key="amount_input_text"
        )

        amount = None
        if raw_amount:
            try:
                amount = float(raw_amount.replace(',', '.'))
                if amount < 0.01:
                    st.error("O valor da venda deve ser maior que R$ 0,00.")
                    amount = None
                else:
                    # Adiciona a exibição do valor formatado logo abaixo da entrada
                    st.info(f"Valor digitado: **R$ {amount:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            except ValueError:
                st.error("Por favor, digite um valor numérico válido para a venda.")
                amount = None

        available_brands = sorted(list(set(list(rates.get('Pag Seguro', {}).keys()) + list(rates.get('Infinity', {}).keys()))))
        display_brands = ['-- Selecione uma bandeira --'] + available_brands

        brand_selection = st.selectbox("💳 **Bandeira do Cartão**", display_brands, key="brand_selector")

        if brand_selection == '-- Selecione uma bandeira --':
            brand = "N/A"
        else:
            brand = brand_selection

        if brand != "N/A":
            m1_installments = list(rates.get('Pag Seguro', {}).get(brand, {}).keys())
            m2_installments = list(rates.get('Infinity', {}).get(brand, {}).keys())
            all_available_installments = sorted(list(set(m1_installments + m2_installments)))
        else:
            all_available_installments = []

        if not all_available_installments:
            installments = st.selectbox("🔢 **Número de Parcelas**", ["N/A"], disabled=True, key="installments_selector_disabled")
        else:
            default_installment_value = 1 if 1 in all_available_installments else all_available_installments[0]
            installments = st.selectbox(
                "🔢 **Número de Parcelas**",
                all_available_installments,
                index=all_available_installments.index(default_installment_value),
                key="installments_selector_enabled"
            )
        
        st.session_state.selected_amount = amount
        st.session_state.selected_brand = brand
        st.session_state.selected_installments = installments

        with st.form("simulation_submit_form"):
            submit_simulation = st.form_submit_button("Simular") # O CSS acima irá estilizar este botão

    def calculate_machine_data(valor_venda, brand_val, qtd_parcela, machine_rates_data):
        if brand_val == "N/A" or qtd_parcela == "N/A" or valor_venda is None or valor_venda <= 0:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        rates_for_brand = machine_rates_data.get(brand_val, {})
        if not rates_for_brand or qtd_parcela not in rates_for_brand:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        taxa = rates_for_brand[qtd_parcela]

        valor_final_venda = valor_venda * (1 + (taxa / 100))
        valor_liquido_venda = valor_venda # O valor líquido que o vendedor recebe é o valor original
        encargos_da_transacao = valor_final_venda - valor_venda
        parcela_cliente = valor_final_venda / qtd_parcela

        return valor_final_venda, parcela_cliente, valor_liquido_venda, encargos_da_transacao, taxa

    if submit_simulation:
        final_amount = st.session_state.selected_amount
        final_brand = st.session_state.selected_brand
        final_installments = st.session_state.selected_installments

        if final_amount is not None and final_amount > 0 and final_brand != "N/A" and final_installments != "N/A":
            st.markdown("<h4 style='text-align: center;'>Resultados da Simulação</h4>", unsafe_allow_html=True)
            
            col1_results, col2_results = st.columns(2) 

            m1_total_client, m1_installment_client, m1_net_seller, m1_transaction_fees, m1_tax_rate = \
                calculate_machine_data(final_amount, final_brand, final_installments, rates.get('Pag Seguro', {}))

            with col1_results:
                st.markdown("<h3 style='text-align: center; color: #F6DF44; font-weight: bolder;'>PagBank</h3>", unsafe_allow_html=True)
                st.markdown("---")
                if m1_total_client != "N/A":
                    st.metric(label="Valor Recebido (EOS)", value=f"R$ {m1_net_seller:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m1_total_client:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m1_installment_client:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Encargos (Cliente)", value=f"R$ {m1_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    # st.metric(label="Taxa Aplicada", value=f"{m1_tax_rate:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    st.warning("Pag Seguro: Dados não disponíveis para esta bandeira/parcelamento.")

            m2_total_client, m2_installment_client, m2_net_seller, m2_transaction_fees, m2_tax_rate = \
                calculate_machine_data(final_amount, final_brand, final_installments, rates.get('Infinity', {}))

            with col2_results:
                st.markdown("<h3 style='text-align: center; color: #17EC2A; font-weight: bolder;'>InfinitePay</h3>", unsafe_allow_html=True)
                st.markdown("---")
                if m2_total_client != "N/A":
                    st.metric(label="Valor Recebido (EOS)", value=f"R$ {m2_net_seller:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m2_total_client:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m2_installment_client:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
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

# --- 5. Função de Logout ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None

# --- Lógica Principal: Condicional de Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_simulator_app()
else:
    login_page()