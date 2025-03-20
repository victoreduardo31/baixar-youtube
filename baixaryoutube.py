import yt_dlp
import tkinter as tk
import logging
import os
import time  # Para trabalhar com o tempo de modificação
from tkinter import messagebox
from PIL import Image, ImageTk  # Para carregar e usar o ícone PNG

# Configuração do logger para salvar os logs na pasta C:\InfoTechStore\log
log_dir = r"C:\InfoTech\BaixarYoutube\log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)  # Cria a pasta log caso ela não exista

log_file = os.path.join(log_dir, "yt_downloader.log")  # Caminho do arquivo de log
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Função para obter o caminho do ffmpeg no diretório fixo
def get_ffmpeg_path():
    # Definir o caminho fixo para o ffmpeg
    ffmpeg_path = r"C:\InfoTech\BaixarYoutube\ffmpeg\bin\ffmpeg.exe"
    return ffmpeg_path

# Função para centralizar a janela
def center_window(window, width, height):
    # Obtém as dimensões da tela
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calcula a posição para centralizar
    position_top = int(screen_height / 2 - height / 2)
    position_right = int(screen_width / 2 - width / 2)

    # Define a geometria da janela (largura x altura + posição no topo + posição à direita)
    window.geometry(f'{width}x{height}+{position_right}+{position_top}')

# Função para obter os melhores formatos disponíveis para download
def get_best_format(url, media_type):
    # Obtém o caminho do ffmpeg a partir da função
    FFMPEG_PATH = get_ffmpeg_path()
    
    ydl_opts = {
        'quiet': True,
        'extractaudio': True,  # Para áudio
        'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',  # Prioriza o melhor formato de áudio ou vídeo
        'noplaylist': True,
        'ffmpeg_location': FFMPEG_PATH,  # Definir o caminho do ffmpeg
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            resolution = None  # Inicializar a variável resolution como None para o caso de áudio
            if media_type == 'audio':
                # Pegando o melhor formato de áudio, considerando a qualidade (bitrate)
                best_format = max(info_dict['formats'], key=lambda x: x.get('abr', 0) if x.get('abr') is not None else 0)
            else:
                # Perguntar se o usuário quer 720p ou 1080p
                available_formats = [fmt for fmt in info_dict['formats'] if fmt.get('height') in [720, 1080]]
                if not available_formats:
                    log_and_display_error("Não há formatos 720p ou 1080p disponíveis.")
                    return None, None, None

                format_choice = messagebox.askquestion("Escolher Resolução", "Deseja baixar em 1080p? Clique em 'Sim' para 1080p ou 'Não' para 720p.")
                if format_choice == 'yes':
                    best_format = max(available_formats, key=lambda x: x.get('height', 0) if x.get('height') == 1080 else 0)
                    resolution = '1080p'
                else:
                    best_format = max(available_formats, key=lambda x: x.get('height', 0) if x.get('height') == 720 else 0)
                    resolution = '720p'

            return best_format, info_dict['title'], resolution  # Retornar também o título e a resolução
    except Exception as e:
        log_and_display_error(f"Erro ao acessar o vídeo: {e}")
        return None, None, None

# Função para obter o caminho da pasta de Downloads do usuário
def get_downloads_folder():
    downloads_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads')
    return downloads_folder

# Função para fazer o download do vídeo ou do áudio em MP3
def download_media(url, media_type):
    best_format, video_title, resolution = get_best_format(url, media_type)

    if not best_format:
        return

    format_choice = best_format['format_id']

    # Se for vídeo, ajustar o nome do arquivo para incluir a resolução
    if media_type == 'video' and resolution:
        video_title = f"{video_title} - {resolution}"

    # Definir a pasta de downloads e o template de nome do arquivo
    downloads_folder = get_downloads_folder()
    output_template = os.path.join(downloads_folder, f'{video_title}.%(ext)s')  # Usar o título do vídeo
    FFMPEG_PATH = get_ffmpeg_path()  # Pega o caminho do ffmpeg

    ydl_opts = {
        'quiet': False,
        'format': format_choice,
        'outtmpl': output_template,  # Salvar na pasta de Downloads
        'ffmpeg_location': FFMPEG_PATH,  # Definir o caminho do ffmpeg
    }

    # Se for para baixar como vídeo, não fazemos o pós-processamento de áudio
    if media_type == 'video':
        ydl_opts.pop('postprocessors', None)
        ydl_opts['noplaylist'] = True  # Evita baixar playlists acidentais

    # Se for para baixar como áudio (MP3), mantemos o pós-processamento
    else:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',      # Garantir que a saída seja MP3
            'preferredquality': '192',    # Defina a qualidade preferida (192kbps)
            'nopostoverwrites': False,    # Permite sobrescrever arquivos existentes
        }]
        ydl_opts['extractaudio'] = True  # Assegura que só o áudio será extraído
        ydl_opts['audioquality'] = 1  # Qualidade máxima de áudio
        ydl_opts['audioformat'] = 'mp3'  # Forçar o formato MP3

        # Evitar a verificação do áudio com ffprobe
        ydl_opts['postprocessor_args'] = [
            '-loglevel', 'quiet',  # Evitar logs excessivos do ffmpeg
            '-acodec', 'libmp3lame',  # Força o codec mp3
            '-ar', '44100',  # Define a taxa de amostragem para 44.1kHz
        ]
        ydl_opts['prefer_ffmpeg'] = True  # Preferir ffmpeg para o pós-processamento

    try:
        # Desabilita o botão e exibe a mensagem de progresso
        download_button.config(state=tk.DISABLED)
        progress_label.config(text="Download em andamento... Aguarde.")
        progress_label.update_idletasks()  # Força o update da interface

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Após o download, obter o nome do arquivo gerado
        downloaded_file = os.path.join(downloads_folder, f"{video_title}.mp4" if media_type == 'video' else f"{video_title}.mp3")

        # Verifica se o arquivo foi criado
        if os.path.exists(downloaded_file):
            current_time = time.time()  # Obtém o tempo atual em segundos desde a época (1970)
            os.utime(downloaded_file, (current_time, current_time))  # Atualiza as datas de modificação e acesso

        # Exibe a mensagem de sucesso quando o download terminar
        messagebox.showinfo("Sucesso", f"Download do {media_type} concluído com sucesso!")
        progress_label.config(text="Download concluído!")
        progress_label.update_idletasks()  # Força o update da interface
        
    except Exception as e:
        log_and_display_error(f"Erro ao fazer o download: {e}")
    finally:
        # Habilita novamente o botão de download e limpa a mensagem de progresso
        download_button.config(state=tk.NORMAL)
        progress_label.config(text="")
        progress_label.update_idletasks()  # Força o update da interface

# Função para logar e exibir os erros
def log_and_display_error(message):
    logging.error(message)
    error_window = tk.Toplevel()
    error_window.title("Erro")

    # Centralizando a janela de erro
    center_window(error_window, 400, 200)

    label = tk.Label(error_window, text="Ocorreu um erro. Veja abaixo:", font=('Arial', 12))
    label.pack(pady=10)

    text_area = tk.Text(error_window, height=10, width=50)
    text_area.insert(tk.END, message)
    text_area.config(state=tk.DISABLED)  # Tornar o campo de texto somente leitura
    text_area.pack(padx=10, pady=10)

    button = tk.Button(error_window, text="Fechar", command=error_window.destroy)
    button.pack(pady=10)

# Função para iniciar o download através da interface gráfica
def download():
    url = url_entry.get()

    if not url:
        log_and_display_error("URL não fornecida pelo usuário.")
        return

    download_type = download_type_var.get()

    if download_type == "Audio":
        download_media(url, "audio")
    elif download_type == "Video":
        download_media(url, "video")
    else:
        log_and_display_error(f"Tipo de download inválido: {download_type}")

# Criando a interface gráfica com tkinter
root = tk.Tk()
root.title("Download do YouTube")

# Centralizar a janela
center_window(root, 410, 200)

# Caminho fixo para o ícone
icon_path = r"C:\InfoTech\BaixarYoutube\youtube.png"  # Defina o caminho fixo para o ícone
if os.path.exists(icon_path):
    icon_image = Image.open(icon_path)
    icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(False, icon_photo)
else:
    print(f"Ícone não encontrado: {icon_path}")

# Label para o link do YouTube
url_label = tk.Label(root, text="Insira o link do vídeo do YouTube:")
url_label.pack()

# Campo de texto para o link
url_entry = tk.Entry(root, width=65, justify='center')
url_entry.pack()

# Opções para o tipo de download
download_type_var = tk.StringVar()
download_type_var.set("Audio")  # Definir valor padrão

audio_button = tk.Radiobutton(root, text="Baixar como MP3", variable=download_type_var, value="Audio")
audio_button.pack()

video_button = tk.Radiobutton(root, text="Baixar como MP4", variable=download_type_var, value="Video")
video_button.pack()

# Botão para iniciar o download
download_button = tk.Button(root, text="Baixar", command=download)
download_button.pack(pady=10)

# Label para exibir o status do download
progress_label = tk.Label(root, text="")
progress_label.pack(pady=5)

root.mainloop()
