# 📚 Sistema de Gerenciamento de Biblioteca

> Projeto desenvolvido para a disciplina de **Tópicos Especiais em Informática** do curso de Análise e Desenvolvimento de Sistemas da **Fatec Ribeirão Preto**.

## 📌 Sobre o Projeto

Este projeto consiste em uma aplicação Web desenvolvida em **Python** utilizando o microframework **Flask**. O sistema tem como objetivo gerenciar o acervo de uma biblioteca, permitindo o controle de autores, livros e usuários do sistema, além de demonstrar interoperabilidade com sistemas externos e manipulação de arquivos.

O projeto foi modelado para atender aos requisitos da avaliação P2 (2-2025), focando em persistência de dados, construção de interfaces gráficas dinâmicas e consumo de APIs.

## 🚀 Funcionalidades

O sistema atende aos seguintes requisitos técnicos:

* **Autenticação e Segurança:**
    * Sistema de Login com proteção de rotas (sessão de usuário).
    * Controle de acesso (apenas usuários logados acessam o painel).
* **Gestão de Dados (CRUD Completo):**
    * **Autores:** Listagem, Cadastro, Edição e Exclusão.
    * **Livros:** Controle de acervo vinculado a autores.
    * **Usuários:** Gerenciamento de quem pode acessar o sistema.
* **Interoperabilidade (Web Service):**
    * **Importação Inteligente:** Conexão com a API da **Open Library** para buscar e cadastrar livros automaticamente baseados no tema "Technology".
* **Manipulação de Arquivos:**
    * **Exportação de Backup:** Gera um arquivo `.zip` contendo todos os dados do banco em formato JSON para download.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework Web:** Flask
* **Banco de Dados:** SQLite 3
* **Frontend:** HTML5, CSS3 e Jinja2 (Renderização Server-Side)
* **Bibliotecas Principais:**
    * `requests` (Consumo de API)
    * `zipfile` & `json` (Manipulação de arquivos)
    * `sqlite3` (Persistência)

## 📦 Pré-requisitos

Para executar este projeto, você precisará ter instalado em sua máquina:

* [Python 3](https://www.python.org/downloads/)
* Pip (Gerenciador de pacotes do Python)

## 🔧 Como Executar

1. **Clone o repositório** (ou baixe os arquivos):
   ```bash
   git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
   cd seu-repositorio

2. **Instale as dependências:** O projeto utiliza bibliotecas externas. Instale-as executando:
    ```bash
    pip install flask requests

3. **Execute a aplicação:**
    ```bash
    python "Projeto P2 - Biblioteca.py"

4. **Acesse no Navegador:** O servidor iniciará localmente. Abra o endereço:
    http://127.0.0.1:5000