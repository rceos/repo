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
# Implementa tratamento robusto de erros e padronização de dados
def carregar_taxas():
    # Dicionário para armazenar taxas processadas
    taxas_carregadas = {
        "Pagbank": {},
        "Cielo": {},
        "Listo": {}
    }
    has_error = False
    
    # Iteração dinâmica sobre máquinas e bandeiras
    for machine, bandeiras in csv_files.items():
        for bandeira, file_path in bandeiras.items():
            try:
                # Carregamento e processamento do CSV
                df = pd.read_csv(file_path, sep=';', encoding='latin1')
                df.columns = ['Parcelas', 'Taxa']
                df['Parcelas'] = df['Parcelas'].astype(int)
                df['Taxa'] = df['Taxa'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                taxas_carregadas[machine][bandeira] = df.set_index('Parcelas')['Taxa'].to_dict()
            except FileNotFoundError:
                # Log de erro para arquivo não encontrado
                st.error(f"Erro: Arquivo '{file_path}' não encontrado. Verifique se os arquivos CSV estão disponíveis.")
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
            
            /* Ocultar sidebar por padrão */
            .css-1d391kg {
                display: none;
            }

            /* Alternativa mais específica */
            section[data-testid="stSidebar"] > div {
                display: none;
            }

            /* Forçar ocultação da sidebar */
            .stSidebar {
                display: none !important;
            }


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
            }
            /* --- CENTRALIZAR st.metric DENTRO DAS COLUNAS --- */
            /* Encontra o contêiner direto do st.metric e aplica flexbox */
            div[data-testid="stMetric"] {
                display: flex;
                flex-direction: column; /* Organiza label e value em coluna */
                align-items: center; /* Centraliza horizontalmente */
                text-align: center; /* Centraliza o texto dentro do metric */
                width: 100%; /* Garante que o metric ocupe a largura total para centralizar */
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
            
            /*-------------*/
            div[data-testid="stMarkdownContainer"] > button > div {
                display: flex;
                justify-content: center;
                width: 50%;
            }
            
            /* Centralizar radio buttons horizontais */
            div[data-testid="stRadio"] > div[role="radiogroup"] {
                display: flex;
                justify-content: center;
                width: 100%;
                gap: 20px;
            }

            div[data-testid="stRadio"] > div[role="radiogroup"] > label {
                margin: 0 10px;
            }


            /* Estilo para a tabela de comparação */
            .comparison-table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            .comparison-table th, .comparison-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            .comparison-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .comparison-table tr:nth-child(even) {
                background-color: #f9f9f9;
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
        bandeiras_disponiveis = sorted(list(set(
            list(taxas.get('Pagbank', {}).keys()) + 
            list(taxas.get('Cielo', {}).keys()) +
            list(taxas.get('Listo', {}).keys())
        )))
        
        display_bandeiras = ['-- Selecione uma bandeira --'] + bandeiras_disponiveis
        bandeira_selecionada = st.selectbox("💳 **Bandeira do Cartão**", display_bandeiras, key="bandeira_selector")
        
        if bandeira_selecionada == '-- Selecione uma bandeira --':
            bandeira = "N/A"
        else:
            bandeira = bandeira_selecionada
        

        # Centralização do modo de exibição
        st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 10px;'><strong>Modo de Exibição</strong></p>", unsafe_allow_html=True)


        # Coluna central maior para o radio button
        col1, col2, col3 = st.columns([0.75, 2.5, 0.75])

        with col2:
            display_mode = st.radio(
                "Modo de Exibição",
                ["Tabela", "Única"],
                horizontal=True,
                key="display_mode",
                label_visibility="collapsed",
                width = "stretch"
            )


        # Lógica para parcelas baseada no modo selecionado
        if bandeira != "N/A":
            m1_parcelas = list(taxas.get('Listo', {}).get(bandeira, {}).keys())
            m2_parcelas = list(taxas.get('Cielo', {}).get(bandeira, {}).keys())
            m3_parcelas = list(taxas.get('Pagbank', {}).get(bandeira, {}).keys())
            parcelas_disponiveis = sorted(list(set(m1_parcelas + m2_parcelas + m3_parcelas)))
        else:
            parcelas_disponiveis = []
        
        # Controle de parcelas baseado no modo de exibição
        if display_mode == "Única":
            if not parcelas_disponiveis:
                parcelas = st.selectbox("🔢 **Número de Parcelas**", ["Selecione um valor"], disabled=True, key="installments_selector_disabled")
            else:
                default_parcela_value = 1 if 1 in parcelas_disponiveis else parcelas_disponiveis[0]
                parcelas = st.selectbox(
                    "🔢 **Número de Parcelas**",
                    parcelas_disponiveis,
                    index=parcelas_disponiveis.index(default_parcela_value),
                    key="installments_selector_enabled"
                )
        else:  # Modo Tabela
            parcelas = "ALL"  # Indica que queremos todas as parcelas
        
        st.session_state.selected_amount = amount
        st.session_state.selected_bandeira = bandeira
        st.session_state.selected_parcelas = parcelas
        st.session_state.selected_display_mode = display_mode
        
        with st.form("simulation_submit_form"):
            submit_simulation = st.form_submit_button("Simular")

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
        valor_final_venda = valor_venda / (1 - taxa)
        
        valor_liquido_venda = valor_venda  # O valor líquido que o vendedor recebe é o valor original
        encargos_da_transacao = valor_final_venda - valor_venda
        parcela_cliente = valor_final_venda / qtd_parcela
        
        return valor_final_venda, parcela_cliente, valor_liquido_venda, encargos_da_transacao, taxa

    def generate_comparison_table(valor_venda, bandeira, parcelas_disponiveis):
        """Gera tabela de comparação para todas as parcelas disponíveis"""
        if not parcelas_disponiveis or valor_venda is None or valor_venda <= 0:
            return None
        
        # Preparar dados para a tabela
        table_data = []
        
        for parcela in parcelas_disponiveis:
            row = {"Parcela": parcela}
            
            # Calcular para Listo
            m1_total, m1_parcela, m1_liquido, m1_encargos, m1_taxa = calculate_machine_data(
                valor_venda, bandeira, parcela, taxas.get('Listo', {})
            )
            
            if m1_parcela != "N/A":
                row["Listo"] = f"R$ {m1_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                row["Listo"] = "---"
            
          
            m2_total, m2_parcela, m2_liquido, m2_encargos, m2_taxa = calculate_machine_data(
                valor_venda, bandeira, parcela, taxas.get('Cielo', {})
            )
            
            if m2_parcela != "N/A":
                row["Cielo"] = f"R$ {m2_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                row["Cielo"] = "---"

            m3_total, m3_parcela, m3_liquido, m3_encargos, m3_taxa = calculate_machine_data(
                valor_venda, bandeira, parcela, taxas.get('Pagbank', {})
            )
            
            if m3_parcela != "N/A":
                row["Pagbank"] = f"R$ {m3_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                row["Pagbank"] = "---"
            
            table_data.append(row)
        
        return table_data

    # Lógica de submissão e processamento da simulação
    if submit_simulation:
        # Recuperação de dados da sessão
        final_amount = st.session_state.selected_amount
        final_bandeira = st.session_state.selected_bandeira
        parcelas_finais = st.session_state.selected_parcelas
        final_display_mode = st.session_state.selected_display_mode
        
        # Validação final antes de processamento
        if final_amount is not None and final_amount > 0 and final_bandeira != "N/A":
            st.markdown("<h3 style='text-align: center;'>Resultados da Simulação</h3>", unsafe_allow_html=True)
            
            if final_display_mode == "Única" and parcelas_finais != "N/A":
                # Modo Única - Exibição original
                col1_results, col2_results, col3_results = st.columns(3)
                
                # Cálculo para diferentes máquinas de cartão
                m1_total_cliente, m1_parcela_cliente, m1_valor_liquido, m1_transaction_fees, m1_tax_rate = \
                    calculate_machine_data(final_amount, final_bandeira, parcelas_finais, taxas.get('Listo', {}))
                
                # Cálculo para Listo
                with col1_results:
                    st.markdown("<h3 style='text-align: center; color: #FFD103; font-weight: bolder;'>Listo</h3>", unsafe_allow_html=True) # <<< MUDANÇA: Título (cor azul como exemplo)
                    st.markdown("---")
                    if m1_total_cliente != "N/A":
                        st.metric(label="Valor Recebido (EOS)", value=f"R$ {m1_valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m1_total_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m1_parcela_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Encargos (Cliente)", value=f"R$ {m1_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    else:
                        st.warning("Listo: Dados não disponíveis para esta bandeira/parcelamento.")

                m2_total_cliente, m2_parcela_cliente, m2_valor_liquido, m2_transaction_fees, m2_tax_rate = \
                    calculate_machine_data(final_amount, final_bandeira, parcelas_finais, taxas.get('Cielo', {}))
                
                # Cálculo para Cielo
                with col2_results:
                    st.markdown("<h3 style='text-align: center; color: #0E749C; font-weight: bolder;'>Cielo</h3>", unsafe_allow_html=True) # <<< MUDANÇA: Título
                    st.markdown("---")
                    if m2_total_cliente != "N/A":
                        st.metric(label="Valor Recebido (EOS)", value=f"R$ {m2_valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m2_total_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m2_parcela_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Encargos (Cliente)", value=f"R$ {m2_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    else:
                        st.warning("Cielo: Dados não disponíveis para esta bandeira/parcelamento.")

                # Cálculo para diferentes máquinas de cartão
                m3_total_cliente, m3_parcela_cliente, m3_valor_liquido, m3_transaction_fees, m3_tax_rate = \
                    calculate_machine_data(final_amount, final_bandeira, parcelas_finais, taxas.get('Pagbank', {}))
                
                # Cálculo para Pagbank
                with col3_results:
                    st.markdown("<h3 style='text-align: center; color: #F5DE3E; font-weight: bolder;'>Pagbank</h3>", unsafe_allow_html=True) # <<< MUDANÇA: Título
                    st.markdown("---")
                    if m3_total_cliente != "N/A":
                        st.metric(label="Valor Recebido (EOS)", value=f"R$ {m3_valor_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Venda (Cliente)", value=f"R$ {m3_total_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Valor da Parcela (Cliente)", value=f"R$ {m3_parcela_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.metric(label="Encargos (Cliente)", value=f"R$ {m3_transaction_fees:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    else:
                        st.warning("Pagbank: Dados não disponíveis para esta bandeira/parcelamento.")
            
            elif final_display_mode == "Tabela":

                if parcelas_disponiveis:
                    table_data = generate_comparison_table(final_amount, final_bandeira, parcelas_disponiveis)
                                
                    if table_data:
                        # Criar colunas para reduzir largura em 1/3 (aproximadamente 67% da largura)
                        table_col_left, table_col_center, table_col_right = st.columns([0.325, 0.35, 0.325])
                                    
                        with table_col_center:
                            # Criar DataFrame para exibição
                            df_comparison = pd.DataFrame(table_data)
                                        
                            # Exibir informações gerais
                            st.info(f"**Valor da venda:** R$ {final_amount:,.2f} | **Bandeira:** {final_bandeira}".replace(",", "X").replace(".", ",").replace("X", "."))
                            
                            # Calcular altura baseada no número de linhas (35px por linha + 50px para cabeçalho)
                            altura_tabela = len(df_comparison) * 35 + 50
                            
                            st.dataframe(
                                df_comparison,
                                use_container_width=True,
                                hide_index=True,
                                height=altura_tabela,  # Altura calculada dinamicamente
                                column_config={
                                    "Parcela": st.column_config.TextColumn(
                                        "Parcelas",
                                        help="Número de parcelas"
                                                            
                                    ),
                                    "PagBank": st.column_config.TextColumn(
                                        "PagBank",
                                        help="Valor da parcela no PagBank"
                                    ),
                                    "InfinitePay": st.column_config.TextColumn(
                                        "InfinitePay",
                                        help="Valor da parcela no InfinitePay"
                                    )
                                }
                            )
                                        
                            # Adicionar observações
                            st.markdown("<h5 style='text-align: center;> **Observações:**</h5>", unsafe_allow_html=True)
                            st.markdown("<p style='text-align: left;'> • Os valores mostrados são o que o <b>cliente pagará</b> por parcela </p>", unsafe_allow_html=True)
                            st.markdown("<p style='text-align: left;'> • Campos com '---' indicam que a opção não está disponível para esta bandeira </p>", unsafe_allow_html=True)
																																 
        else:
            # Criar colunas para centralizar e reduzir largura do info
            warning_col_left, warning_col_center, warning_col_right = st.columns([0.25, 0.5, 0.25])
            with warning_col_center:
                st.warning("Por favor, preencha todos os campos corretamente (Valor e Bandeira) antes de simular.")

    
    st.markdown("---")
    st.markdown("<p style='text-align: right;'>by Douglas Corrêa</p>", unsafe_allow_html=True)
    

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