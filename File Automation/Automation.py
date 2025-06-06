from os import scandir, rename
from os.path import splitext, exists, join
from shutil import move
from time import sleep

import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#Directories being used to call and relocate files  
source_dir = "C:\\Users\\bartl\\Downloads"
dest_image = "C:\\Users\\bartl\\Downloads\\Downloaded Pictures"
dest_music = "C:\\Users\\bartl\\Downloads\\Downloaded Music"
dest_video = "C:\\Users\\bartl\\Downloads\\Downloaded Videos"
dest_document = "C:\\Users\\bartl\\Downloads\\Downloaded Documents"
dest_comp = "C:\\Users\\bartl\\Downloads\\Downloaded Zip Files"
dest_app = "C:\\Users\\bartl\Downloads\\Downloaded Applications"

#Image types
image_extensions = [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp", ".tiff", ".tif", ".psd", ".raw", ".arw", ".cr2", ".nrw",
                    ".k25", ".bmp", ".dib", ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2", ".j2k", ".jpf", ".jpf", ".jpx", ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"]

#Compression Types
compression_extensions = [".7z", ".s7z", ".ace", ".afa", ".alz", ".apk", ".arc", "ark", ".arc", "cdx", ".arj", ".b1", ".b6z", ".ba", ".bh", ".cab", ".car", ".cfs",	".cpt",	".dar",	".dd", ".dgc",	
                          ".dmg", ".ear", ".gca", ".genozip", ".ha", ".hki", ".ice", ".jar", ".kgb", ".lzh", ".lha", ".lzx", ".pak", ".partimg", ".paq6", ".paq7", ".paq8", ".pea", ".phar", ".pim", 
                          ".pit", ".qda", ".rar", ".rk", ".sda", ".sea", ".sen", ".sqx", ".tar", ".uc", ".uc0", ".uc2", ".ucn", ".ur2", ".ue2",	".uca",	".uha",	".war",	".wim",	".xar",	".xp3",	".yz1",	
                          ".zip", ".zipx",	".zoo",	".zpaq", ".zz"]

#Executable File Types
application_extensions = [".ipa", ".xbe", ".jar", ".apk", ".ahk", ".bin", ".exe", ".bat", ".widget", ".app", ".com", ".sh",	".scr",	".command",	".ex_",	".exe1", ".server"]

#Video types
video_extensions = [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg",
                    ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf", ".avchd"]
#Audio types
music_extensions = [".m4a", ".flac", "mp3", ".wav", ".wma", ".aac"]

#Document types
document_extensions = [".doc", ".docx", ".odt",
                       ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"]

#Function to be called by move_file, allows for file names to be viewed and changed
def unique_name(dest, name):
    filename, extension = splitext(name)
    counter = 1
    #Add number to the end of a file name if the file already exists
    while exists(f"{dest}/{name}"):
        name = f"{filename}({str(counter)}){extension}"
        counter += 1
    return name

#Function used to rename files as they are moved
def move_file(dest, entry, name):
    if exists(f"{dest}/{name}"):
        file_name = unique_name(dest, name)
        oldName = join(dest, name)
        newName = join(dest, file_name)
        rename(oldName, newName)
    move(entry, dest)
        
        

#Class being used to move files and rename them
class FileMover(FileSystemEventHandler):
    def on_modified(self, event):
        with scandir(source_dir) as entries:
            for entry in entries:
                name = entry.name
                self.get_image_files(entry, name)
                self.get_video_files(entry,name)
                self.get_music_files(entry,name)
                self.get_document_files(entry,name)
                self.get_compression_files(entry,name)
                self.get_application_files(entry,name)
                
    def get_image_files(self, entry, name): #Looks for image files in the source_dir and then moves them to the assigned folder
        for image_extension in image_extensions:
            if name.endswith(image_extension) or name.endswith(image_extension.upper()):
                move_file(dest_image, entry, name)
                logging.info(f"Image file: {name} was moved")
                
    def get_video_files(self, entry, name): #Looks for video files in the source_dir and then moves them to the assigned folder
        for video_extension in video_extensions:
            if name.endswith(video_extension) or name.endswith(video_extension.upper()):   
                move_file(dest_video, entry, name)
                logging.info(f"Video file: {name} was moved")
               
    def get_music_files(self, entry, name): #Looks for music files in the source_dir and then moves them to the assigned folder
        for music_extension in music_extensions:
            if name.endswith(music_extension) or name.endswith(music_extension.upper()):
                move_file(dest_music, entry, name)
                logging.info(f"Audio file: {name} was moved")
                
    def get_document_files(self, entry, name): #Looks for document files in the source_dir and then moves them to the assigned folder
        for document_extension in document_extensions:
            if name.endswith(document_extension) or name.endswith(document_extension.upper()):
                move_file(dest_document, entry, name)
                logging.info(f"Document file: {name} was moved")
                        
    def get_compression_files(self, entry, name): #Looks for compression files in the source_dir and then moves them to the assigned folder
        for compression_extension in compression_extensions:
            if name.endswith(compression_extension) or name.endswith(compression_extension.upper()):
                move_file(dest_comp, entry, name)
                logging.info(f"Compression file: {name} was moved")

    def get_application_files(self, entry, name): #Looks for application files in the source_dir and then moves them to the assigned folder
        for application_extension in application_extensions:
            if name.endswith(application_extension) or name.endswith(application_extension.upper()):
                move_file(dest_app, entry, name)
                logging.info(f"Application file: {name} was moved")
                
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = source_dir
    event_handler = FileMover()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()               
    
    
    
    