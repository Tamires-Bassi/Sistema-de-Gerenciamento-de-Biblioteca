import sqlite3
import os
import io
import json
import zipfile
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file, flash

# ==============================================================================
# CONFIGURAÇÕES E SETUP
# ==============================================================================
#Gerenciar Livros
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura' 
DB_NAME = 'biblioteca_projeto.db'

# URL da Open Library para buscar livros sobre "technology" (ou qualquer tema)
# O parâmetro 'limit=10' garante que não sobrecarregamos o sistema
URL_IMPORTACAO = "https://openlibrary.org/search.json?q=technology&limit=10"

# ==============================================================================
# CAMADA DE DADOS (BANCO DE DADOS)
# ==============================================================================
#def menu
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabela Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabela Autores
    c.execute('''
        CREATE TABLE IF NOT EXISTS autores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nacionalidade TEXT
        )
    ''')
    
    # Tabela Livros
    c.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            ano INTEGER,
            autor_id INTEGER,
            FOREIGN KEY (autor_id) REFERENCES autores (id)
        )
    ''')
    
    # Usuário Admin Padrão
    c.execute('SELECT * FROM usuarios WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', ('admin', 'admin'))

    conn.commit()
    conn.close()

# ==============================================================================
# CAMADA DE INTERFACE (HTML + JINJA2)
# ==============================================================================

html_base = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema Biblioteca - Fatec</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f4f4f9; color: #333; }
        header { background-color: #2c3e50; color: white; padding: 15px; text-align: center; }
        nav { background-color: #34495e; padding: 10px; text-align: center; }
        nav a { color: white; text-decoration: none; margin: 0 15px; font-weight: bold; }
        nav a:hover { text-decoration: underline; }
        .container { max-width: 1000px; margin: 20px auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #2c3e50; }
        table { width: 1000px; border-collapse: collapse; margin-top: 20px; width: 100%; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #2980b9; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .btn { padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin: 2px; }
        .btn-primary { background-color: #27ae60; color: white; }
        .btn-warning { background-color: #f39c12; color: white; }
        .btn-danger { background-color: #c0392b; color: white; }
        .btn-info { background-color: #2980b9; color: white; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="password"], input[type="number"], select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .alert { padding: 10px; background-color: #f8d7da; color: #721c24; border-radius: 4px; margin-bottom: 15px; }
        .success { background-color: #d4edda; color: #155724; }
        footer { text-align: center; margin-top: 40px; padding: 20px; font-size: 0.8em; color: #777; }
    </style>
</head>
<body>
    <header>
        <h1>Sistema de Gerenciamento de Biblioteca</h1>
    </header>
    {% if session.get('user_id') %}
    <nav>
        <a href="{{ url_for('menu') }}">Menu Principal</a>
        <a href="{{ url_for('listar_autores') }}">Autores</a>
        <a href="{{ url_for('listar_livros') }}">Livros</a>
        <a href="{{ url_for('importar_dados') }}">Importação Web</a>
        <a href="{{ url_for('sobre') }}">Sobre</a>
        <a href="{{ url_for('logout') }}" style="color: #e74c3c;">Sair</a>
    </nav>
    {% endif %}
    
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert success">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- BLOCO_CONTEUDO -->
    </div>

    <footer>
        Projeto de Tópicos Especiais em Informática - 2025
    </footer>
</body>
</html>
"""

def render_page(content_html, **kwargs):
    full_template = html_base.replace('<!-- BLOCO_CONTEUDO -->', content_html)
    return render_template_string(full_template, **kwargs)

# ==============================================================================
# ROTAS E LÓGICA
# ==============================================================================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('menu'))
        else:
            return render_page("""
            <h2>Login do Sistema</h2>
            <div class="alert">Usuário ou senha inválidos. Tente (admin/admin)</div>
            <form method="post" style="max-width: 400px; margin: 0 auto;">
                <div class="form-group">
                    <label>Usuário:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%">Entrar</button>
            </form>
            """)
            
    return render_page("""
    <div style="text-align: center; padding: 50px;">
        <h2>Bem-vindo</h2>
        <p>Por favor, faça login para continuar.</p>
        <form method="post" style="max-width: 300px; margin: 0 auto; text-align: left;">
            <div class="form-group">
                <label>Usuário:</label>
                <input type="text" name="username" placeholder="admin" required>
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" name="password" placeholder="admin" required>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%">Entrar</button>
        </form>
    </div>
    """)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/menu')
def menu():
    if not session.get('user_id'): return redirect(url_for('login'))
    return render_page("""
    <h2>Menu Principal</h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div style="background: #eaf2f8; padding: 20px; border-radius: 8px;">
            <h3>Gerenciar Autores</h3>
            <p>Cadastre, edite e remova autores.</p>
            <a href="{{ url_for('listar_autores') }}" class="btn btn-info">Acessar</a>
        </div>
        <div style="background: #eaf2f8; padding: 20px; border-radius: 8px;">
            <h3>Gerenciar Livros</h3>
            <p>Controle o acervo de livros.</p>
            <a href="{{ url_for('listar_livros') }}" class="btn btn-info">Acessar</a>
        </div>
        <div style="background: #fef9e7; padding: 20px; border-radius: 8px;">
            <h3>Importação Web</h3>
            <p>Buscar livros na Open Library.</p>
            <a href="{{ url_for('importar_dados') }}" class="btn btn-warning">Acessar</a>
        </div>
        <div style="background: #fef9e7; padding: 20px; border-radius: 8px;">
            <h3>Exportação</h3>
            <p>Baixar backup completo em ZIP.</p>
            <a href="{{ url_for('exportar_dados') }}" class="btn btn-warning">Exportar Dados</a>
        </div>
            <div style="background: #e8f8f5; padding: 20px; border-radius: 8px;">
            <h3>Gerenciar Usuários</h3>
            <p>Controle de acesso ao sistema.</p>
            <a href="{{ url_for('listar_usuarios') }}" class="btn btn-primary">Acessar</a>
        </div>
                       
    </div>
    """)

@app.route('/sobre')
def sobre():
    if not session.get('user_id'): return redirect(url_for('login'))
    return render_page("""
    <h2>Sobre o Projeto</h2>
    <p style="text-align: justify; line-height: 1.6;">
            Este projeto tem como objetivo desenvolver uma aplicação Web completa utilizando a linguagem <strong>Python</strong> e o microframework <strong>Flask</strong>. 
            O sistema visa solucionar o controle de acervos bibliográficos, permitindo o gerenciamento persistente de autores, livros e usuários através de um banco de dados relacional.
        </p>
        <p style="text-align: justify; line-height: 1.6;">
            Além das operações fundamentais de cadastro (CRUD), a aplicação demonstra interoperabilidade de sistemas ao consumir dados externos da API pública da <em>Open Library</em> e oferece funcionalidades avançadas de backup (importação e exportação de dados em JSON/ZIP).
        </p>
    <hr>
    <h3>Desenvolvedores</h3>
    <ul>
        <li><strong>Nome:</strong> [Tamires de Sousa Bassi] | <strong>RA:</strong> [22840482523039]
    </ul>
    """)

# ==================== CRUD AUTORES ====================

@app.route('/autores')
def listar_autores():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    autores = conn.execute('SELECT * FROM autores').fetchall()
    conn.close()
    return render_page("""
    <h2>Lista de Autores</h2>
    <a href="{{ url_for('criar_autor') }}" class="btn btn-primary">+ Novo Autor</a>
    <table>
        <tr><th>ID</th><th>Nome</th><th>Nacionalidade</th><th>Ações</th></tr>
        {% for autor in autores %}
        <tr>
            <td>{{ autor['id'] }}</td>
            <td>{{ autor['nome'] }}</td>
            <td>{{ autor['nacionalidade'] }}</td>
            <td>
                <a href="{{ url_for('editar_autor', id=autor['id']) }}" class="btn btn-warning">Editar</a>
                <a href="{{ url_for('deletar_autor', id=autor['id']) }}" class="btn btn-danger" onclick="return confirm('Confirmar?')">Excluir</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    """, autores=autores)

@app.route('/autores/novo', methods=('GET', 'POST'))
def criar_autor():
    if not session.get('user_id'): return redirect(url_for('login'))
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO autores (nome, nacionalidade) VALUES (?, ?)', (request.form['nome'], request.form['nacionalidade']))
        conn.commit()
        conn.close()
        flash('Autor criado!')
        return redirect(url_for('listar_autores'))
    return render_page("""
    <h2>Novo Autor</h2>
    <form method="post"><div class="form-group"><label>Nome:</label><input type="text" name="nome" required></div>
    <div class="form-group"><label>Nacionalidade:</label><input type="text" name="nacionalidade"></div>
    <button type="submit" class="btn btn-primary">Salvar</button></form>
    """)

@app.route('/autores/<int:id>/editar', methods=('GET', 'POST'))
def editar_autor(id):
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    autor = conn.execute('SELECT * FROM autores WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        conn.execute('UPDATE autores SET nome = ?, nacionalidade = ? WHERE id = ?', (request.form['nome'], request.form['nacionalidade'], id))
        conn.commit()
        conn.close()
        flash('Atualizado!')
        return redirect(url_for('listar_autores'))
    conn.close()
    return render_page("""
    <h2>Editar Autor</h2>
    <form method="post"><div class="form-group"><label>Nome:</label><input type="text" name="nome" value="{{ autor['nome'] }}"></div>
    <div class="form-group"><label>Nacionalidade:</label><input type="text" name="nacionalidade" value="{{ autor['nacionalidade'] }}"></div>
    <button type="submit" class="btn btn-primary">Atualizar</button></form>
    """, autor=autor)

@app.route('/autores/<int:id>/deletar')
def deletar_autor(id):
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM autores WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Deletado!')
    return redirect(url_for('listar_autores'))

# ==================== CRUD LIVROS ====================

@app.route('/livros')
def listar_livros():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    livros = conn.execute('SELECT livros.*, autores.nome as autor_nome FROM livros LEFT JOIN autores ON livros.autor_id = autores.id').fetchall()
    conn.close()
    return render_page("""
    <h2>Acervo de Livros</h2>
    <a href="{{ url_for('criar_livro') }}" class="btn btn-primary">+ Novo Livro</a>
    <table>
        <tr><th>ID</th><th>Título</th><th>Ano</th><th>Autor</th><th>Ações</th></tr>
        {% for livro in livros %}
        <tr>
            <td>{{ livro['id'] }}</td>
            <td>{{ livro['titulo'] }}</td>
            <td>{{ livro['ano'] }}</td>
            <td>{{ livro['autor_nome'] if livro['autor_nome'] else 'Desconhecido' }}</td>
            <td>
                <a href="{{ url_for('editar_livro', id=livro['id']) }}" class="btn btn-warning">Editar</a>
                <a href="{{ url_for('deletar_livro', id=livro['id']) }}" class="btn btn-danger" onclick="return confirm('Confirmar?')">Excluir</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    """, livros=livros)

@app.route('/livros/novo', methods=('GET', 'POST'))
def criar_livro():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('INSERT INTO livros (titulo, ano, autor_id) VALUES (?, ?, ?)', 
                     (request.form['titulo'], request.form['ano'], request.form['autor_id']))
        conn.commit()
        conn.close()
        flash('Livro criado!')
        return redirect(url_for('listar_livros'))
    autores = conn.execute('SELECT * FROM autores').fetchall()
    conn.close()
    return render_page("""
    <h2>Novo Livro</h2>
    <form method="post"><div class="form-group"><label>Título:</label><input type="text" name="titulo" required></div>
    <div class="form-group"><label>Ano:</label><input type="number" name="ano"></div>
    <div class="form-group"><label>Autor:</label><select name="autor_id">{% for a in autores %}<option value="{{a['id']}}">{{a['nome']}}</option>{% endfor %}</select></div>
    <button type="submit" class="btn btn-primary">Salvar</button></form>
    """, autores=autores)

@app.route('/livros/<int:id>/editar', methods=('GET', 'POST'))
def editar_livro(id):
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    livro = conn.execute('SELECT * FROM livros WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        conn.execute('UPDATE livros SET titulo = ?, ano = ?, autor_id = ? WHERE id = ?', 
                     (request.form['titulo'], request.form['ano'], request.form['autor_id'], id))
        conn.commit()
        conn.close()
        flash('Atualizado!')
        return redirect(url_for('listar_livros'))
    autores = conn.execute('SELECT * FROM autores').fetchall()
    conn.close()
    return render_page("""
    <h2>Editar Livro</h2>
    <form method="post"><div class="form-group"><label>Título:</label><input type="text" name="titulo" value="{{ livro['titulo'] }}"></div>
    <div class="form-group"><label>Ano:</label><input type="number" name="ano" value="{{ livro['ano'] }}"></div>
    <div class="form-group"><label>Autor:</label><select name="autor_id">
    {% for a in autores %}<option value="{{a['id']}}" {% if a['id'] == livro['autor_id'] %}selected{% endif %}>{{a['nome']}}</option>{% endfor %}
    </select></div>
    <button type="submit" class="btn btn-primary">Atualizar</button></form>
    """, livro=livro, autores=autores)

@app.route('/livros/<int:id>/deletar')
def deletar_livro(id):
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM livros WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Deletado!')
    return redirect(url_for('listar_livros'))

# ==================== IMPORTAÇÃO INTELIGENTE (OPEN LIBRARY) ====================

@app.route('/importar', methods=['GET', 'POST'])
def importar_dados():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    livros_recentes = []
    
    if request.method == 'POST':
        try:
            print("Buscando dados na Open Library...")
            response = requests.get(URL_IMPORTACAO)
            dados = response.json()
            
            count = 0
            for item in dados.get('docs', []):
                titulo = item.get('title', 'Sem Título')
                # Pega o primeiro autor ou define Desconhecido
                nome_autor = item.get('author_name', ['Desconhecido'])[0]
                ano = item.get('first_publish_year', 0)
                
                # 1. Verifica se o autor já existe, se não, cria
                autor = conn.execute('SELECT id FROM autores WHERE nome = ?', (nome_autor,)).fetchone()
                if not autor:
                    cur = conn.execute('INSERT INTO autores (nome, nacionalidade) VALUES (?, ?)', (nome_autor, 'Estrangeiro'))
                    autor_id = cur.lastrowid
                else:
                    autor_id = autor['id']
                
                # 2. Verifica se o livro já existe no acervo principal
                existe = conn.execute('SELECT id FROM livros WHERE titulo = ?', (titulo,)).fetchone()
                
                if not existe:
                    # 3. Insere DIRETAMENTE na tabela oficial de livros
                    conn.execute('INSERT INTO livros (titulo, ano, autor_id) VALUES (?, ?, ?)', (titulo, ano, autor_id))
                    count += 1
                    livros_recentes.append({'titulo': titulo, 'autor': nome_autor, 'ano': ano})
            
            conn.commit()
            if count > 0:
                flash(f'Sucesso! {count} livros foram adicionados ao seu acervo oficial.')
            else:
                flash('Nenhum livro novo encontrado (todos já estavam no banco).')
                
        except Exception as e:
            flash(f'Erro na conexão: {str(e)}')
    
    conn.close()
    
    return render_page("""
    <h2>Importação Automática (Open Library)</h2>
    <p>Esta função busca livros na internet e <strong>adiciona automaticamente</strong> ao seu menu "Livros".</p>
    <p>Conectando em: <code>openlibrary.org</code> buscando por "Technology"</p>
    
    <form method="post" style="margin-bottom: 20px;">
        <button type="submit" class="btn btn-primary">Buscar e Adicionar ao Acervo</button>
    </form>
    
    {% if livros_recentes %}
    <h3>Acabaram de ser adicionados:</h3>
    <ul>
        {% for l in livros_recentes %}
        <li><strong>{{ l['titulo'] }}</strong> ({{ l['ano'] }}) - {{ l['autor'] }}</li>
        {% endfor %}
    </ul>
    <p><a href="{{ url_for('listar_livros') }}" class="btn btn-info">Ver todos em Gerenciar Livros</a></p>
    {% endif %}
    """, livros_recentes=livros_recentes)

@app.route('/exportar')
def exportar_dados():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    dados = {
        "usuarios": [dict(r) for r in conn.execute('SELECT id, username FROM usuarios').fetchall()],
        "autores": [dict(r) for r in conn.execute('SELECT * FROM autores').fetchall()],
        "livros": [dict(r) for r in conn.execute('SELECT * FROM livros').fetchall()]
    }
    conn.close()
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('backup_biblioteca.json', json.dumps(dados, indent=4))
    memory_file.seek(0)
    
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='backup_completo.zip')

# ==================== CRUD USUÁRIOS (ADICIONADO PARA COMPLETAR REQUISITOS) ====================

@app.route('/usuarios')
def listar_usuarios():
    if not session.get('user_id'): return redirect(url_for('login'))
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    return render_page("""
    <h2>Gerenciamento de Usuários</h2>
    <a href="{{ url_for('criar_usuario') }}" class="btn btn-primary">+ Novo Usuário</a>
    <table>
        <tr><th>ID</th><th>Username</th><th>Ações</th></tr>
        {% for u in usuarios %}
        <tr>
            <td>{{ u['id'] }}</td>
            <td>{{ u['username'] }}</td>
            <td>
                {% if u['username'] != 'admin' %}
                <a href="{{ url_for('deletar_usuario', id=u['id']) }}" class="btn btn-danger" onclick="return confirm('Tem certeza que deseja remover este usuário?')">Excluir</a>
                {% else %}
                <span style="color: grey; font-style: italic;">(Sistema)</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    """, usuarios=usuarios)

@app.route('/usuarios/novo', methods=('GET', 'POST'))
def criar_usuario():
    if not session.get('user_id'): return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash(f'Usuário {username} criado com sucesso!')
            return redirect(url_for('listar_usuarios'))
        except sqlite3.IntegrityError:
            flash('Erro: Nome de usuário já existe!')
        finally:
            conn.close()
            
    return render_page("""
    <h2>Novo Usuário</h2>
    <form method="post">
        <div class="form-group">
            <label>Nome de Usuário:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Senha:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Salvar Usuário</button>
        <a href="{{ url_for('listar_usuarios') }}" class="btn btn-warning">Cancelar</a>
    </form>
    """)

@app.route('/usuarios/<int:id>/deletar')
def deletar_usuario(id):
    if not session.get('user_id'): return redirect(url_for('login'))
    
    # Impede que o usuário se delete (opcional, mas recomendado)
    if id == session.get('user_id'):
        flash('Você não pode excluir a si mesmo enquanto está logado!')
        return redirect(url_for('listar_usuarios'))

    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Usuário removido!')
    return redirect(url_for('listar_usuarios'))

if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
        print("Banco de dados criado com nova estrutura.")
    app.run(debug=True)