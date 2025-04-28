# Importações necessárias
import streamlit as st
import pandas as pd
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image, ExifTags
import altair as alt
import time
from datetime import datetime
import os
import uuid
import base64

# Configuração da página
st.set_page_config(
    page_title="Sistema QR Code Inventário",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #008000;
        margin-bottom: 0px;
        text-align: center;
    }
    .sub-header {
        font-size: 18px;
        color: #6B7280;
        margin-top: 0px;
        margin-bottom: 30px;
        text-align: center;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #008000 !important;
        color: white !important;
    }
    div[data-testid="stForm"] {
        border: 1px solid #6B7280;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    div[data-testid="stVerticalBlock"] {
        padding-top: 12px;
        padding-bottom: 12px;
    }
    button[kind="primaryFormSubmit"] {
        background-color: #008000;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    button[kind="secondaryFormSubmit"] {
        background-color: #6B7280;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    div[data-testid="column"] {
        padding: 10px;
    }
    .success-msg {
        background-color: #008000;
        border-left: 5px solid #10B981;
        padding: 15px;
        border-radius: 5px;
    }
    .warning-msg {
        background-color: #F91E;
        border-left: 5px solid #F59E0B;
        padding: 15px;
        border-radius: 5px;
    }
    .error-msg {
        background-color: #F45E81;
        border-left: 5px solid #EF4444;
        padding: 15px;
        border-radius: 5px;
    }
    .info-msg {
        background-color: #6B7280;
        border-left: 5px solid #3B82F6;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
def load_data():
    """Carrega os dados do arquivo CSV ou cria um novo se não existir"""
    if os.path.exists("inventario.csv"):
        return pd.read_csv("inventario.csv")
    else:
        # Criar arquivo com colunas padrão
        df = pd.DataFrame(columns=["codigo", "nome", "descricao", "categoria", "quantidade", "data_cadastro"])
        df.to_csv("inventario.csv", index=False)
        return df

def add_item(codigo, nome, descricao, categoria="Outros", quantidade=1):
    """Adiciona um novo item ao CSV"""
    df = load_data()
    nova_linha = {
        "codigo": codigo,
        "nome": nome,
        "descricao": descricao,
        "categoria": categoria,
        "quantidade": quantidade,
        "data_cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    df.to_csv("inventario.csv", index=False)
    return nova_linha

def buscar_item(codigo):
    """Busca um item pelo código"""
    df = load_data()
    resultado = df[df["codigo"] == codigo]
    if len(resultado) > 0:
        return resultado.iloc[0].to_dict()
    else:
        return None

def scan_qr_code(image):
    """Escaneia QR Code com detecção de orientação"""
    # Verificar e corrigir orientação da imagem
    if isinstance(image, Image.Image):
        try:
            # Tentar obter informações de orientação
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            
            exif = image._getexif()
            if exif is not None:
                exif_orientation = exif.get(orientation)
                
                # Corrigir orientação baseado no valor EXIF
                if exif_orientation == 2:
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                elif exif_orientation == 3:
                    image = image.transpose(Image.ROTATE_180)
                elif exif_orientation == 4:
                    image = image.transpose(Image.FLIP_TOP_BOTTOM)
                elif exif_orientation == 5:
                    image = image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
                elif exif_orientation == 6:
                    image = image.transpose(Image.ROTATE_270)
                elif exif_orientation == 7:
                    image = image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
                elif exif_orientation == 8:
                    image = image.transpose(Image.ROTATE_90)
        except (AttributeError, KeyError, IndexError):
            # Se não conseguir obter/processar EXIF, continuar assim mesmo
            pass
        
        # Converter para formato OpenCV
        img = np.array(image.convert('RGB'))
        img = img[:, :, ::-1].copy()  # Converter RGB para BGR
    else:
        return None
    
    # Tentar decodificar normalmente
    decoded_objects = decode(img)
    
    # Se não detectar nada, tentar com rotações adicionais
    if not decoded_objects:
        # Testar 90 graus
        img_90 = np.rot90(img)
        decoded_objects = decode(img_90)
        
        # Testar 180 graus
        if not decoded_objects:
            img_180 = np.rot90(img_90)
            decoded_objects = decode(img_180)
            
            # Testar 270 graus
            if not decoded_objects:
                img_270 = np.rot90(img_180)
                decoded_objects = decode(img_270)
    
    if decoded_objects:
        # Retornar o primeiro QR code encontrado
        return decoded_objects[0].data.decode('utf-8')
    else:
        return None

def mostrar_item_card(item):
    """Exibe as informações do item em um card estilizado"""
    categorias_icones = {
        "Painel": "📱",
        "Relé": "📟",
        "Ferramentas": "🔧",
        "Amplificador": "⚙️",
        "Outros": "📦"
    }
    
    icone = categorias_icones.get(item['categoria'], "📦")
    
    st.markdown(f"""
    <div class="card">
        <h3 style="color: #008000;">{icone} {item['nome']}</h3>
        <p style="color: #6B7280; font-style: italic;">Código: {item['codigo']}</p>
        <hr style="margin: 12px 0; border-color: #6B7280;">
        <p><strong>Descrição:</strong><br>{item['descricao']}</p>
        <div style="display: flex; justify-content: space-between; margin-top: 20px;">
            <span><strong>Categoria:</strong> {item['categoria']}</span>
            <span><strong>Quantidade:</strong> {item['quantidade']}</span>
        </div>
        <p style="font-size: 12px; color: #6B7280; text-align: right; margin-top: 10px;">
            Cadastrado em: {item['data_cadastro']}
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_stats():
    """Obtém estatísticas para o painel"""
    df = load_data()
    total_items = len(df)
    
    # Cadastros de hoje
    hoje = datetime.now().strftime("%Y-%m-%d")
    cadastros_hoje = len(df[df['data_cadastro'].str.startswith(hoje)])
    
    # Categorias
    categorias = df['categoria'].value_counts().to_dict() if 'categoria' in df.columns else {}
    
    return total_items, cadastros_hoje, categorias

# Interface principal
st.markdown('<p class="main-header">SISTEMA DE INVENTÁRIO QR CODE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Escaneie, busque e cadastre itens facilmente</p>', unsafe_allow_html=True)

# Sidebar com estatísticas
with st.sidebar:
    st.markdown('<p style="font-size: 24px; font-weight: bold; color: #008000; text-align: center;">PAINEL DE CONTROLE</p>', unsafe_allow_html=True)
    
    # Estatísticas
    st.markdown("### 📊 Estatísticas")
    total_items, cadastros_hoje, categorias = get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Total de Itens", total_items)
    col2.metric("Cadastros Hoje", cadastros_hoje)
    
    # Filtros e outras opções
    st.markdown("### 🔍 Opções")
    if st.button("🔄 Atualizar Dados"):
        st.rerun()
    
    if st.button("📤 Exportar Dados"):
        # Lógica para exportar
        df = load_data()
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # Converter para base64
        href = f'<a href="data:file/csv;base64,{b64}" download="inventario.csv">Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # Sobre
    st.markdown("### ℹ️ Sobre")
    st.markdown("""
    <div class="info-msg">
    Este sistema permite o gerenciamento de inventário através de QR Codes. 
    Escaneie, busque e cadastre itens de forma rápida e eficiente.
    </div>
    """, unsafe_allow_html=True)

# Conteúdo principal com abas
tab1, tab2, tab3 = st.tabs(["📷 Escaneamento", "🔍 Busca Manual", "📊 Dashboard"])

# Aba de escaneamento
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Escolha como escanear")
        upload_option = st.radio(
            "Selecione o método:",
            ["Capturar com Câmera (Habilite as permissões)", "Upload de Imagem"]
        )
        
        if upload_option == "Upload de Imagem":
            uploaded_file = st.file_uploader("Carregue a imagem com QR Code", type=["jpg", "jpeg", "png"])
        else:
            camera_image = st.camera_input("Tire uma foto do QR Code")
            uploaded_file = camera_image
    
    with col2:
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            
            # Mostrar a imagem original
            st.image(image, caption="Imagem enviada", use_container_width=True)
            
            # Adiciona uma mensagem de processamento
            with st.spinner("🔍 Processando QR code..."):
                time.sleep(0.7)  # Pequeno delay para efeito visual
                qr_data = scan_qr_code(image)
            
            if qr_data:
                st.markdown(f'<div class="success-msg">✅ QR Code detectado: {qr_data}</div>', unsafe_allow_html=True)
                
                # Consultar o banco de dados CSV
                item = buscar_item(qr_data)
                
                if item is not None:
                    # Mostrar as informações do item existente
                    st.markdown('<div class="success-msg">✅ Item encontrado na base de dados!</div>', unsafe_allow_html=True)
                    mostrar_item_card(item)
                else:
                    # Interface para registrar novo item
                    st.markdown('<div class="warning-msg">⚠️ Item não encontrado. Deseja cadastrar este item?</div>', unsafe_allow_html=True)
                    
                    with st.form("novo_item_upload"):
                        st.markdown("### 📝 Dados do Novo Item")
                        nome = st.text_input("Nome do item", placeholder="Digite um nome descritivo")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            categoria = st.selectbox("Categoria", ["Painel", "Relé", "Ferramentas", "Amplificador", "Outros"])
                        with col2:
                            quantidade = st.number_input("Quantidade", min_value=1, value=1)
                        
                        descricao = st.text_area("Descrição detalhada", placeholder="Descreva as características do item...")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            submitted = st.form_submit_button("💾 Cadastrar")
                        with col2:
                            cancelled = st.form_submit_button("❌ Cancelar")
                        
                        if submitted and nome:
                            # Salvar novo item no CSV
                            novo_item = add_item(qr_data, nome, descricao, categoria, quantidade)
                            st.markdown('<div class="success-msg">✅ Item cadastrado com sucesso! Clique em Cadastrar para fazer um novo cadastro.</div>', unsafe_allow_html=True)
                            mostrar_item_card(novo_item)
            else:
                st.markdown("""
                <div class="error-msg">
                    ❌ Nenhum QR Code detectado na imagem. Tente uma foto com melhor iluminação ou posicionamento.
                </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                <div class="info-msg">
                    💡 Dicas: Certifique-se que o QR code está bem visível e não está muito inclinado. Caso preferir, pode tirar uma foto do QR Code e fazer o upload da imagem, ou fazer a busca manual.
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Aba de busca manual
# Correção para a parte da aba de busca manual

with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Checar estado de sessão ou inicializar se não existir
    if 'mostrar_formulario_cadastro' not in st.session_state:
        st.session_state.mostrar_formulario_cadastro = False
    if 'codigo_para_cadastro' not in st.session_state:
        st.session_state.codigo_para_cadastro = ""
    
    # Formulário de busca/cadastro inicial
    if not st.session_state.mostrar_formulario_cadastro:
        st.markdown("### 🔎 Buscar ou Cadastrar Item")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            codigo_busca = st.text_input("Código do item - (Aproxime a câmera do celular ao QRCode e visualize o código)", placeholder="Digite ou escaneie o código")
        
        with col2:
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                if st.button("🔍 Buscar", key="buscar_btn"):
                    if codigo_busca:
                        item = buscar_item(codigo_busca)
                        if item is not None:
                            st.session_state.resultado_busca = True
                            st.session_state.item_encontrado = item
                        else:
                            st.session_state.resultado_busca = False
                            st.session_state.item_nao_encontrado = True
            
            with col2_2:
                if st.button("➕ Cadastrar", key="cadastrar_btn"):
                    if codigo_busca:
                        # Verificar se já existe
                        item = buscar_item(codigo_busca)
                        if item is not None:
                            st.session_state.item_ja_existe = True
                            st.session_state.item_encontrado = item
                        else:
                            # Configurar para mostrar formulário de cadastro
                            st.session_state.codigo_para_cadastro = codigo_busca
                            st.session_state.mostrar_formulario_cadastro = True
    else:
        # Formulário de cadastro
        st.markdown(f"""
        <div class="info-msg">
        📝 Cadastrando novo item com código: <strong>{st.session_state.codigo_para_cadastro}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        nome = st.text_input("Nome do item", placeholder="Digite um nome descritivo")
        
        col1, col2 = st.columns(2)
        with col1:
            categoria = st.selectbox("Categoria", ["Painel", "Relé", "Ferramentas", "Amplificador", "Outros"])
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
        
        descricao = st.text_area("Descrição detalhada", placeholder="Descreva as características do item...")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Cadastrar", key="salvar_item_btn"):
                if nome:
                    # Salvar novo item no CSV
                    novo_item = add_item(st.session_state.codigo_para_cadastro, nome, descricao, categoria, quantidade)
                    st.session_state.mostrar_formulario_cadastro = False
                    st.session_state.item_cadastrado = True
                    st.session_state.novo_item = novo_item
        
        with col2:
            if st.button("❌ Cancelar", key="cancelar_btn"):
                st.session_state.mostrar_formulario_cadastro = False
    
    # Mostrar resultados da busca ou confirmação de cadastro após ações
    if 'resultado_busca' in st.session_state and st.session_state.resultado_busca:
        st.markdown('<div class="success-msg">✅ Item encontrado na base de dados!</div>', unsafe_allow_html=True)
        mostrar_item_card(st.session_state.item_encontrado)
        # Limpar estado após mostrar
        del st.session_state.resultado_busca
        del st.session_state.item_encontrado
    
    if 'item_nao_encontrado' in st.session_state and st.session_state.item_nao_encontrado:
        st.markdown('<div class="error-msg">❌ Item não encontrado com este código.</div>', unsafe_allow_html=True)
        # Limpar estado após mostrar
        del st.session_state.item_nao_encontrado
    
    if 'item_ja_existe' in st.session_state and st.session_state.item_ja_existe:
        st.markdown(f'<div class="warning-msg">⚠️ Este código já está cadastrado para outro item.</div>', unsafe_allow_html=True)
        mostrar_item_card(st.session_state.item_encontrado)
        # Limpar estado após mostrar
        del st.session_state.item_ja_existe
        del st.session_state.item_encontrado
    
    if 'item_cadastrado' in st.session_state and st.session_state.item_cadastrado:
        st.markdown('<div class="success-msg">✅ Item cadastrado com sucesso! Clique em Cadastrar para fazer o cadastro de um novo item.</div>', unsafe_allow_html=True)
        mostrar_item_card(st.session_state.novo_item)
        # Limpar estado após mostrar
        del st.session_state.item_cadastrado
        del st.session_state.novo_item
    
    st.markdown('</div>', unsafe_allow_html=True)

# Aba de dashboard
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    st.markdown("### 📊 Análise de Inventário")
    
    df = load_data()
    
    if len(df) > 0:
        # Converter a coluna de data para datetime
        if 'data_cadastro' in df.columns:
            df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])
            
            # Gráfico de itens por categoria
            if 'categoria' in df.columns:
                st.markdown("#### Distribuição por Categoria")
                categoria_counts = df['categoria'].value_counts().reset_index()
                categoria_counts.columns = ['categoria', 'contagem']
                
                chart = alt.Chart(categoria_counts).mark_bar().encode(
                    x=alt.X('categoria:N', title='Categoria', sort='-y'),
                    y=alt.Y('contagem:Q', title='Quantidade de Itens'),
                    color=alt.Color('categoria:N', legend=None)
                ).properties(
                    height=300
                )
                
                st.altair_chart(chart, use_container_width=True)
            
            # Gráfico de cadastros por mês
            st.markdown("#### Histórico de Cadastros")
            df['mes'] = df['data_cadastro'].dt.strftime('%Y-%m')
            cadastros_por_mes = df.groupby('mes').size().reset_index(name='contagem')
            
            line_chart = alt.Chart(cadastros_por_mes).mark_line(point=True).encode(
                x=alt.X('mes:N', title='Mês', sort=None),
                y=alt.Y('contagem:Q', title='Itens Cadastrados'),
                tooltip=['mes', 'contagem']
            ).properties(
                height=300
            )
            
            st.altair_chart(line_chart, use_container_width=True)
            
            # Exibir tabela de itens
            st.markdown("#### Lista de Itens Cadastrados")
            
            # Converter de volta para exibição
            if 'data_cadastro' in df.columns:
                df['data_cadastro'] = df['data_cadastro'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Colunas para exibir
            colunas_exibir = ['codigo', 'nome', 'categoria', 'quantidade', 'data_cadastro']
            df_exibir = df[colunas_exibir] if all(col in df.columns for col in colunas_exibir) else df
            
            st.dataframe(df_exibir, use_container_width=True)
    else:
        st.markdown("""
        <div class="info-msg">
        📊 Nenhum dado disponível para análise. Cadastre itens para visualizar estatísticas.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; border-top: 1px solid #E5E7EB; color: #6B7280;">
    Sistema de Inventário QR Code © 2025<br>
    Versão 1.0.0
</div>
""", unsafe_allow_html=True)
