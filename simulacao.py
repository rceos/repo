# Importações necessárias para o projeto de simulação de cartão
import streamlit as st
import pandas as pd
import json
import io

# Configuração da página: Layout amplo e título identificador
st.set_page_config(layout="wide", page_title="Simulador de Cartão - EOS")

# Carregamento seguro de credenciais de utilizador
# Tratamento flexível para nomes com espaços
USERS = {k.replace('_', ' '): v for k, v in st.secrets["users"].items()}

# Mapeamento de ficheiros de taxas por máquina e bandeira
csv_files = {
    "Pagbank": {
        "Visa": "dataset/Maquina_Pagbank - Visa.CSV",
        "Master": "dataset/Maquina_Pagbank - Master.CSV",
        "Diners": "dataset/Maquina_Pagbank - Diners.CSV",
        "Demais": "dataset/Maquina_Pagbank - Demais.CSV",
    },
    "Cielo": {
        "Visa": "dataset/Maquina_Cielo - Visa.CSV",
        "Master": "dataset/Maquina_Cielo - Master.CSV",
        "Link de Pagamento": "dataset/Maquina_Cielo - Link.CSV",
    },
    "Listo": {
        "Visa": "dataset/Maquina_Listo - Visa.CSV",
        "Master": "dataset/Maquina_Listo - Master.CSV",
        "Elo": "dataset/Maquina_Listo - Elo.CSV",
        "Link de Pagamento": "dataset/Maquina_Listo - Link.CSV",
    }
}

# Função central de carregamento de taxas
def carregar_taxas():
    taxas_carregadas = {
        "Pagbank": {},
        "Cielo": {},
        "Listo": {}
    }
    has_error = False
    
    for machine, bandeiras in csv_files.items():
        for bandeira, file_path in bandeiras.items():
            try:
                df = pd.read_csv(file_path, sep=';', encoding='latin1')
                df.columns = ['Parcelas', 'Taxa']
                df['Parcelas'] = df['Parcelas'].astype(int)
                df['Taxa'] = df['Taxa'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                taxas_carregadas[machine][bandeira] = df.set_index('Parcelas')['Taxa'].to_dict()
            except FileNotFoundError:
                st.error(f"Erro: Ficheiro '{file_path}' não encontrado.")
                has_error = True
            except Exception as e:
                st.error(f"Erro ao carregar o ficheiro '{file_path}': {e}")
                has_error = True
    
    return taxas_carregadas if not has_error else None

if 'loaded_rates' not in st.session_state:
    st.session_state.loaded_rates = carregar_taxas()

if st.session_state.loaded_rates is None:
    st.warning("Não foi possível carregar todas as taxas.")
    st.stop()

taxas = st.session_state.loaded_rates

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None

def login_page():
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    login_col_l, login_col_c, login_col_r = st.columns([1, 1, 1])
    with login_col_c:
        with st.form("login_form"):
            username = st.text_input("Utilizador")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Utilizador ou senha incorretos.")

def main_simulator_app():
    # Estilos CSS corrigidos para Temas Light/Dark e alinhamento da tabela
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }

            /* Estilo das Métricas */
            div[data-testid="stMetricLabel"] p {
                font-size: 1.1rem;
                font-weight: bold;
                color: gray;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.5rem;
                font-weight: bolder;
            }
            div[data-testid="stMetric"] {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                width: 100%;
            }

            /* Botão Simular */
            div[data-testid="stFormSubmitButton"] > button {
                background-color: #FF8C00;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                width: 100%;
            }

            /* Radio Buttons Centralizados */
            div[data-testid="stRadio"] > div[role="radiogroup"] {
                display: flex;
                justify-content: center;
                gap: 20px;
            }

            /* --- ESTILO DA TABELA (Compatível com Light/Dark) --- */
            .styled-table {
                width: 100%;
                border-collapse: collapse;
                color: var(--text-color);
                margin-bottom: 20px;
            }
            .styled-table th, .styled-table td {
                border: 1px solid rgba(128, 128, 128, 0.3);
                padding: 8px 12px;
                position: relative;
                min-width: 90px;
                color: var(--text-color);
            }
            .styled-table th {
                background-color: rgba(128, 128, 128, 0.1);
                text-align: center;
                font-weight: bold;
            }
            
            /* Coluna Parcela centralizada */
            .styled-table th:first-child,
            .styled-table td:first-child {
                text-align: center;
                min-width: 50px;
            }
            
            /* R$ à esquerda, valor à direita - Agora acompanhando a cor do texto sem opacidade */
            .currency {
                position: absolute;
                left: 10px;
                opacity: 1.0; /* Removida a opacidade 0.6 para acompanhar a cor do texto */
                font-size: 0.9em;
                color: var(--text-color);
            }
            .amount {
                display: block;
                text-align: right;
                color: var(--text-color);
            }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>Simulador de Cartão</h2>", unsafe_allow_html=True)
    st.sidebar.button("Sair", on_click=logout)
    
    col_spacer_l, col_center, col_spacer_r = st.columns([1, 1.2, 1])
    
    with col_center:
        raw_amount = st.text_input("💰 **Valor da Venda (R$)**", placeholder="Ex: 5.000,00")
        amount = None
        if raw_amount:
            try:
                amount = float(raw_amount.replace('.', '').replace(',', '.'))
                st.info(f"Valor: **R$ {amount:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            except:
                st.error("Valor inválido.")

        bandeiras_disponiveis = sorted(list(set(
            list(taxas.get('Pagbank', {}).keys()) + 
            list(taxas.get('Cielo', {}).keys()) +
            list(taxas.get('Listo', {}).keys())
        )))
        
        bandeira = st.selectbox("💳 **Bandeira do Cartão**", ['-- Selecione --'] + bandeiras_disponiveis)
        
        # Modo de Exibição na mesma linha e centralizado
        col_label, col_radio = st.columns([1, 2])
        with col_label:
            st.markdown("<p style='font-weight: bold; margin-top: 15px; text-align: right;'>Modo de Exibição</p>", unsafe_allow_html=True)
        with col_radio:
            display_mode = st.radio("Modo", ["Tabela", "Única"], horizontal=True, label_visibility="collapsed")

        if display_mode == "Única" and bandeira != '-- Selecione --':
            all_parcelas = sorted(list(set(
                list(taxas.get('Listo', {}).get(bandeira, {}).keys()) + 
                list(taxas.get('Cielo', {}).get(bandeira, {}).keys()) +
                list(taxas.get('Pagbank', {}).get(bandeira, {}).keys())
            )))
            parcela_sel = st.selectbox("🔢 **Número de Parcelas**", all_parcelas)
        else:
            parcela_sel = "ALL"
        
        with st.form("simulation_submit_form"):
            submit_simulation = st.form_submit_button("Simular")

    def calculate_machine_data(valor, bandeira_valor, qtd, machine_rates):
        rates = machine_rates.get(bandeira_valor, {})
        if not rates or qtd not in rates or not valor:
            return "N/A", "N/A", "N/A", "N/A"
        taxa = rates[qtd]
        # Mantendo a lógica de cálculo original do simulacao5.py
        total = valor / (1 / (1 + taxa))
        parcela = total / qtd
        return total, parcela, valor, (total - valor)

    def generate_comparison_table(valor, band):
        if not valor or band == '-- Selecione --': return None
        
        def format_cell(val):
            if val == "N/A": return "<span class='amount'>---</span>"
            txt = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"<span class='currency'>R$</span><span class='amount'>{txt}</span>"

        all_p = sorted(list(set(
            list(taxas.get('Listo', {}).get(band, {}).keys()) + 
            list(taxas.get('Cielo', {}).get(band, {}).keys()) +
            list(taxas.get('Pagbank', {}).get(band, {}).keys())
        )))

        table_data = []
        for p in all_p:
            row = {"Parcela": p}
            _, p1, _, _ = calculate_machine_data(valor, band, p, taxas.get('Listo', {}))
            row["Listo"] = format_cell(p1)
            _, p2, _, _ = calculate_machine_data(valor, band, p, taxas.get('Cielo', {}))
            row["Cielo"] = format_cell(p2)
            _, p3, _, _ = calculate_machine_data(valor, band, p, taxas.get('Pagbank', {}))
            row["Pagbank"] = format_cell(p3)
            table_data.append(row)
        return table_data

    if submit_simulation and amount and bandeira != '-- Selecione --':
        st.markdown("<h3 style='text-align: center;'>Resultados da Simulação</h3>", unsafe_allow_html=True)
        
        if display_mode == "Única":
            c1, c2, c3 = st.columns(3)
            # Listo
            t1, p1, l1, f1 = calculate_machine_data(amount, bandeira, parcela_sel, taxas.get('Listo', {}))
            with c1:
                st.markdown("<h3 style='text-align: center; color: #FFD103;'>Listo</h3>", unsafe_allow_html=True)
                if t1 != "N/A":
                    st.metric("EOS recebe", f"R$ {l1:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Cliente paga (total)", f"R$ {t1:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Parcela", f"R$ {p1:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                else: st.warning("Dados indisponíveis")
            # Cielo
            t2, p2, l2, f2 = calculate_machine_data(amount, bandeira, parcela_sel, taxas.get('Cielo', {}))
            with c2:
                st.markdown("<h3 style='text-align: center; color: #0E749C;'>Cielo</h3>", unsafe_allow_html=True)
                if t2 != "N/A":
                    st.metric("EOS recebe", f"R$ {l2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Cliente paga (total)", f"R$ {t2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Parcela", f"R$ {p2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                else: st.warning("Dados indisponíveis")
            # Pagbank
            t3, p3, l3, f3 = calculate_machine_data(amount, bandeira, parcela_sel, taxas.get('Pagbank', {}))
            with c3:
                st.markdown("<h3 style='text-align: center; color: #F5DE3E;'>Pagbank</h3>", unsafe_allow_html=True)
                if t3 != "N/A":
                    st.metric("EOS recebe", f"R$ {l3:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Cliente paga (total)", f"R$ {t3:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.metric("Parcela", f"R$ {p3:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                else: st.warning("Dados indisponíveis")
        else:
            table_data = generate_comparison_table(amount, bandeira)
            if table_data:
                # Ajuste de colunas para centralizar e estreitar a tabela (40% da largura total)
                col_l, col_m, col_r = st.columns([0.3, 0.4, 0.3])
                with col_m:
                    df = pd.DataFrame(table_data)
                    html_table = df.to_html(classes='styled-table', index=False, escape=False, border=0)
                    st.markdown(html_table, unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.8em; opacity: 0.7;'>• Valores que o cliente pagará por parcela.<br>• '---' indica opção indisponível.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='text-align: right; font-size: 0.8em;'>by Douglas Corrêa</p>", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if st.session_state.logged_in: main_simulator_app()
else: login_page()