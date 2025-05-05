# Extrator de Categorias da Shopee via API

Este projeto é um script Python para extrair todas as categorias do catálogo da Shopee Brasil usando a API interna da plataforma. Os dados extraídos são salvos em arquivos CSV, Excel e também podem ser enviados diretamente para um banco de dados PostgreSQL.

## Funcionalidades
- Extração automática de todas as categorias da Shopee (multi-nível)
- Salvamento dos dados em CSV e Excel
- Upload automático dos dados para um banco PostgreSQL
- Log detalhado do processo
- Uso de variáveis de ambiente para segurança das credenciais

## Como usar

### 1. Clonar o repositório
```bash
git clone https://github.com/ikkimaximos/shopee.git
cd shopee
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar o arquivo `.env`
Crie um arquivo chamado `.env` na raiz do projeto com as informações do seu banco PostgreSQL:

```
POSTGRES_HOST=seu_host
POSTGRES_DB=seu_banco
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_PORT=5432
```

### 4. Executar o script
```bash
python shopee.py
```

Os dados serão salvos em:
- `categorias_shopee_api.csv`
- `categorias_shopee_api.xlsx`
- Tabela `categorias_shopee` no seu banco PostgreSQL

## Estrutura da Tabela no PostgreSQL
A tabela criada terá o seguinte cabeçalho:

| categoria | subcategoria | 3_nivel_categoria | 4_nivel_categoria | 5_nivel_categoria | id_categoria | imagem_categoria |
|-----------|--------------|-------------------|-------------------|-------------------|--------------|-----------------|

## Observações
- O script faz uso de logs detalhados em `extrator_api_shopee.log`.
- As credenciais do banco nunca ficam expostas no código.
- Caso a tabela já exista, ela será substituída (comportamento padrão).

## Licença
MIT

---

Dúvidas ou sugestões? Abra uma issue no repositório! 