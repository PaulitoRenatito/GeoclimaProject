# 🚀 Coletor de Dados Meteorológicos (Projeto Geoclima)

Um script em Python que automatiza a coleta de dados diários de estações meteorológicas do INMET, processa as informações e as salva em uma planilha Excel (`.xlsx`) limpa, organizada e pronta para análise.

---

## ✅ Funcionalidades Principais

-   **Busca por Data Específica**: Configure facilmente o dia para o qual os dados devem ser coletados.
-   **Coleta em Massa**: Consulta dezenas de estações de uma só vez, de forma automatizada.
-   **Exportação Inteligente para Excel**: Gera uma planilha `.xlsx` nativa, com tipos de dados corretos (números são números, não texto), colunas selecionadas e cabeçalhos renomeados para fácil leitura.
-   **Interface Amigável**: Exibe uma barra de progresso em tempo real durante a coleta.
-   **Design Resiliente**: Se a consulta a uma estação falhar, o script registra o erro e continua com as próximas, sem interromper todo o processo.

---

## ⚙️ Primeiros Passos: Instalação e Configuração

Siga os passos abaixo para deixar o ambiente pronto para execução.

### 1. Pré-requisitos

-   **Python**: Versão 3.11 ou superior é recomendada para máxima compatibilidade.
-   **Token da API do INMET**: Um token de acesso é necessário para fazer as consultas. Você pode obter o seu gratuitamente no [Portal do Desenvolvedor do INMET](https://portal.inmet.gov.br/dev).

### 2. Preparação do Ambiente

1.  **Clone o Repositório**
    Clone ou baixe os arquivos deste projeto para o seu computador.

2.  **Instale as Dependências**
    Abra um terminal na pasta raiz do projeto e execute o comando abaixo. Ele instalará todas as bibliotecas necessárias (`pandas`, `requests`, etc.).
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuração do Projeto

Antes da primeira execução, dois arquivos precisam ser configurados:

1.  **Seu Token de Acesso (Segredo)**
    Por segurança, o token fica em uma pasta `env/` que é ignorada pelo Git. Você precisa criá-la manualmente.

    -   **Passo 1:** Na raiz do projeto, **crie uma nova pasta** chamada `env`.
    -   **Passo 2:** **Copie** o arquivo `secrets.py.example` (que está na raiz) para **dentro** da pasta `env`.
    -   **Passo 3:** **Renomeie** o arquivo copiado para `secrets.py`.
    -   **Passo 4:** Abra o novo arquivo `env/secrets.py` e substitua `"SEU_TOKEN_AQUI"` pelo seu token real.

    A estrutura final deve ser esta:
    ```
    GeoclimaProject/
    ├── env/
    │   └── secrets.py  <-- Seu token está aqui
    ├── main.py
    └── ...
    ```

2.  **Parâmetros da Busca**
    -   Abra o arquivo `config.py`.
    -   Altere a variável `DATA_DA_BUSCA` para a data que você deseja consultar, usando o formato `"AAAA-MM-DD"`.

---

## ▶️ Como Executar

Com tudo configurado, abra o terminal na raiz do projeto e execute o script principal:

```bash
python main.py
```

O script iniciará o processo, exibindo a barra de progresso. Ao final, uma mensagem de sucesso será exibida e sua planilha será salva na pasta `excel/`, com um nome no formato `AAAA_MM_DD.xlsx`.

---

## 🔧 Solução de Problemas Comuns

-   **`ImportError: No module named 'pandas'` (ou outro módulo)**
    > **Causa**: As dependências não foram instaladas corretamente.
    > **Solução**: Certifique-se de que você executou `pip install -r requirements.txt` no ambiente virtual correto do seu projeto.

-   **`ImportError: cannot import name 'token' from 'secrets'`**
    > **Causa**: O arquivo `env/secrets.py` não foi criado ou configurado corretamente.
    > **Solução**: Siga atentamente os 4 passos na seção "Seu Token de Acesso (Segredo)". Verifique se a pasta se chama `env` e o arquivo `secrets.py`.

-   **O script roda, mas nenhum arquivo é gerado.**
    > **Causa**: A API do INMET pode não ter retornado dados para a data consultada.
    > **Solução**: Verifique no terminal se a mensagem "Nenhum dado foi coletado" foi exibida. Tente executar para uma data diferente.