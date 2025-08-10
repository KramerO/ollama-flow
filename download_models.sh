#!/bin/bash

# Modell Download Script für ZLUDA/llama.cpp
# Ausführen mit: bash download_models.sh

set -e

# Farben für bessere Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Modell-Verzeichnis
MODELS_DIR="/home/oliver/projects/ollama-flow/models"
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo "========================================"
echo "  Modell Download für ZLUDA/llama.cpp"
echo "========================================"
echo ""

# Verfügbare Modelle
show_available_models() {
    echo "Verfügbare Modelle:"
    echo ""
    echo "1. Phi-3 Mini (4K) - ~2.4GB (Empfohlen für Tests)"
    echo "2. Llama 3.2 3B - ~2.0GB (Schnell, gut für Chat)"
    echo "3. Llama 2 7B Chat - ~3.8GB (Ausgewogen)"
    echo "4. CodeLlama 7B - ~3.8GB (Gut für Code-Generierung)"
    echo "5. Mistral 7B Instruct - ~4.1GB (Sehr gut für Instructions)"
    echo "6. Alle kleinen Modelle (1-3)"
    echo "0. Beenden"
    echo ""
}

# Modell herunterladen
download_model() {
    local url=$1
    local filename=$2
    local description=$3
    
    if [ -f "$filename" ]; then
        print_warning "$filename bereits vorhanden, überspringe Download"
        return 0
    fi
    
    print_status "Lade $description herunter..."
    print_status "URL: $url"
    print_status "Datei: $filename"
    
    wget -c -O "$filename" "$url"
    
    if [ -f "$filename" ]; then
        print_success "$description erfolgreich heruntergeladen"
        print_status "Dateigröße: $(du -h "$filename" | cut -f1)"
    else
        echo "Fehler beim Download von $description"
        return 1
    fi
}

# Test eines Modells
test_model() {
    local model_file=$1
    
    if [ ! -f "$model_file" ]; then
        echo "Modell $model_file nicht gefunden!"
        return 1
    fi
    
    print_status "Teste Modell: $model_file"
    
    # Umgebung für ZLUDA setzen
    export ZLUDA_PATH="/opt/zluda"
    export LD_LIBRARY_PATH="/opt/zluda/lib:$LD_LIBRARY_PATH"
    export CUDA_VISIBLE_DEVICES="0"
    
    cd "/home/oliver/projects/ollama-flow/llama.cpp"
    
    echo "Test-Prompt wird ausgeführt..."
    ./llama-cli \
        -m "../models/$model_file" \
        -p "Hello! Can you introduce yourself briefly?" \
        -n 50 \
        --gpu-layers 35 \
        --batch-size 512 \
        --threads 4
}

# Hauptmenü
main_menu() {
    while true; do
        show_available_models
        read -p "Wähle ein Modell (0-6): " choice
        
        case $choice in
            1)
                download_model \
                    "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf" \
                    "phi-3-mini-4k-instruct-q4.gguf" \
                    "Phi-3 Mini 4K Instruct"
                ;;
            2)
                download_model \
                    "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" \
                    "llama-3.2-3b-instruct-q4.gguf" \
                    "Llama 3.2 3B Instruct"
                ;;
            3)
                download_model \
                    "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" \
                    "llama-2-7b-chat-q4.gguf" \
                    "Llama 2 7B Chat"
                ;;
            4)
                download_model \
                    "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf" \
                    "codellama-7b-instruct-q4.gguf" \
                    "CodeLlama 7B Instruct"
                ;;
            5)
                download_model \
                    "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
                    "mistral-7b-instruct-v0.2-q4.gguf" \
                    "Mistral 7B Instruct v0.2"
                ;;
            6)
                print_status "Lade alle kleinen Modelle herunter..."
                download_model \
                    "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf" \
                    "phi-3-mini-4k-instruct-q4.gguf" \
                    "Phi-3 Mini 4K Instruct"
                download_model \
                    "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" \
                    "llama-3.2-3b-instruct-q4.gguf" \
                    "Llama 3.2 3B Instruct"
                download_model \
                    "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf" \
                    "llama-2-7b-chat-q4.gguf" \
                    "Llama 2 7B Chat"
                ;;
            0)
                break
                ;;
            *)
                echo "Ungültige Auswahl. Bitte wähle 0-6."
                ;;
        esac
        
        echo ""
        read -p "Möchtest du ein weiteres Modell herunterladen? (j/n): " continue_choice
        if [[ $continue_choice != "j" && $continue_choice != "J" ]]; then
            break
        fi
        echo ""
    done
}

# Nach Download testen?
ask_test() {
    echo ""
    print_status "Verfügbare Modelle im Verzeichnis:"
    ls -la *.gguf 2>/dev/null || echo "Keine GGUF-Modelle gefunden"
    
    echo ""
    read -p "Möchtest du ein Modell testen? (j/n): " test_choice
    
    if [[ $test_choice == "j" || $test_choice == "J" ]]; then
        echo ""
        echo "Verfügbare Modelle:"
        ls -1 *.gguf 2>/dev/null | nl
        echo ""
        read -p "Wähle Modell-Nummer: " model_num
        
        model_file=$(ls -1 *.gguf 2>/dev/null | sed -n "${model_num}p")
        if [ -n "$model_file" ]; then
            test_model "$model_file"
        else
            echo "Ungültige Modell-Nummer"
        fi
    fi
}

# Script ausführung
echo "Aktuelles Verzeichnis: $MODELS_DIR"
echo ""

main_menu
ask_test

echo ""
print_success "Modell-Download abgeschlossen!"
echo ""
echo "Verwende die Modelle mit:"
echo "python main.py --use-zluda --ollama-model 'phi-3-mini-4k-instruct-q4' --task 'Deine Aufgabe'"
echo "oder:"
echo "python main.py --config config_zluda.json --task 'Deine Aufgabe'"