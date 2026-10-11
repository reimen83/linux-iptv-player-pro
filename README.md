# Linux IPTV Player Pro 📺

Um player de IPTV moderno e leve desenvolvido em Python 3 e PyQt6, otimizado para sistemas Linux. Possui suporte a listas M3U/M3U8 e integração nativa com a API Xtream Codes (Ao Vivo, Filmes VOD e Séries).

## 🚀 Funcionalidades

- **Multi-Aba**: Divisão organizada em Canais Ao Vivo, Filmes & VOD, Séries e Conteúdo Adulto.
- **Filtro Adulto Automático**: Isolamento de conteúdo +18 em aba própria via correspondência de palavras-chave.
- **Suporte Xtream Codes**: Autenticação via API com salvamento seguro das credenciais locais (`config_xtream.json`).
- **Controlo On-Demand**: Barra de progresso/tempo (*seek bar*) funcional para filmes e séries.
- **Detecção de Legendas**: Seleção dinâmica de faixas de legenda embarcadas no fluxo de vídeo.
- **Modo Tela Cheia**: Alternância limpa para tela cheia (100% de preenchimento de vídeo) acionada por botão, duplo clique ou tecla **ESC**.

## 🛠️ Requisitos e Dependências

Certifique-se de ter o **VLC** instalado no sistema (necessário para a biblioteca `python-vlc`):

```bash
sudo apt update
sudo apt install vlc -y

Bibliotecas Python
Instale as dependências listadas no requirements.txt:

Bash
pip install -r requirements.txt

💻 Como Executar
Bash
python3 player_iptv.py