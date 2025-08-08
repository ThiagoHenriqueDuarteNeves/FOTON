"""
Interface Gráfica para o Agente de QA Automatizado
Permite configurar URL, passos e instruções customizadas para o LLM
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import sys
import io
from pathlib import Path

# Importar as funções do main
from main import agente_explorador, obter_modelos_disponiveis

# Variável global para acessar a UI
current_ui_instance = None

class RedirectText:
    """Classe para redirecionar output do console para a UI (thread-safe)"""
    def __init__(self, text_widget, tag):
        self.text_widget = text_widget
        self.tag = tag

    def _append(self, string):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string, self.tag)
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)

    def write(self, string):
        # Garante atualização no main thread do Tkinter
        try:
            self.text_widget.after(0, self._append, string)
        except Exception:
            pass

    def flush(self):
        pass

class AgenteUI:
    def __init__(self, root):
        global current_ui_instance
        current_ui_instance = self  # Definir instância global
        
        self.root = root
        self.root.title("🤖 Agente de QA Automatizado - Instruções Customizadas")
        
        # Iniciar maximizada
        self.root.state('zoomed')  # Windows maximizado
        
        # Configurar dimensões mínimas
        self.root.minsize(800, 600)
        
        # Permitir redimensionamento
        self.root.resizable(True, True)
        
        # Variáveis de controle
        self.is_running = False
        self.current_thread = None
        self.stop_requested = False  # Flag para parar execução
        
        # Configurar estilo com fallback de tema
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            try:
                style.theme_use('vista')
            except Exception:
                # Deixa o tema padrão
                pass
        
        self.setup_ui()
        self.setup_console_redirect()
        
    def setup_ui(self):
        # PanedWindow para criar a divisão redimensionável
        paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Frame superior para todos os controles
        controls_frame = ttk.Frame(paned_window, padding="10")
        paned_window.add(controls_frame, weight=0) # Peso 0 para não expandir

        # Frame inferior para o console
        console_pane = ttk.Frame(paned_window, padding=(10, 5))
        paned_window.add(console_pane, weight=1) # Peso 1 para expandir
        
        # --- Layout dos Controles ---
        controls_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Título
        title_label = ttk.Label(controls_frame, text="🤖 Agente de QA Automatizado", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        # URL
        url_label = ttk.Label(controls_frame, text="🔗 URL:")
        url_label.grid(row=row, column=0, sticky=tk.W, pady=2)
        
        self.url_var = tk.StringVar(value="https://concursos.cesgranrio.org.br/portal")
        url_entry = ttk.Entry(controls_frame, textvariable=self.url_var)
        url_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)
        row += 1
        
        # Max Passos
        passos_label = ttk.Label(controls_frame, text="🔢 Max Passos:")
        passos_label.grid(row=row, column=0, sticky=tk.W, pady=2)
        
        self.max_passos_var = tk.StringVar(value="10")
        passos_entry = ttk.Entry(controls_frame, textvariable=self.max_passos_var, width=10)
        passos_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Modelo LLM
        modelo_label = ttk.Label(controls_frame, text="🤖 Modelo LLM:")
        modelo_label.grid(row=row, column=0, sticky=tk.W, pady=2)
        
        # Frame para modelo com botão de atualizar
        modelo_frame = ttk.Frame(controls_frame)
        modelo_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)
        modelo_frame.columnconfigure(0, weight=1)
        
        self.modelo_var = tk.StringVar(value="qwen/qwen2.5-vl-7b")
        self.modelo_combo = ttk.Combobox(modelo_frame, textvariable=self.modelo_var, width=25, state="readonly")
        self.modelo_combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Botão para atualizar lista de modelos
        refresh_btn = ttk.Button(modelo_frame, text="🔄", width=3, command=self.atualizar_modelos)
        refresh_btn.grid(row=0, column=1)
        
        # Carregar modelos inicialmente
        self.carregar_modelos()
        row += 1
        
        # Instruções
        inst_frame = ttk.LabelFrame(controls_frame, text="🎯 Instruções Customizadas para o LLM", padding="5")
        inst_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        inst_frame.columnconfigure(0, weight=1)
        
        exemplos_text = (
            '• "Procure por editais de concursos públicos federais. Evite links de contato."\n'
            '• "Navegue até a área de inscrições. Clique apenas em concursos com inscrições abertas."'
        )
        exemplos_label = ttk.Label(inst_frame, text=exemplos_text, justify=tk.LEFT, foreground="gray")
        exemplos_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.instructions_text = scrolledtext.ScrolledText(
            inst_frame, height=4, wrap=tk.WORD, font=("Arial", 10)
        )
        self.instructions_text.grid(row=1, column=0, sticky="ew")
        row += 1
        
        # Botões
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(buttons_frame, text="🚀 Iniciar", command=self.start_agent, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(buttons_frame, text="⏹️ Parar", command=self.stop_agent, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(buttons_frame, text="🗑️ Limpar", command=self.clear_logs)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(buttons_frame, text="💾 Salvar", command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Status e Progress bar
        status_frame = ttk.Frame(controls_frame)
        status_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(5,0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Aguardando...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5,0))

        # --- Layout do Console ---
        console_pane.rowconfigure(0, weight=1)
        console_pane.columnconfigure(0, weight=1)
        
        logs_frame = ttk.LabelFrame(console_pane, text="📋 Logs em Tempo Real", padding="5")
        logs_frame.grid(row=0, column=0, sticky="nsew")
        logs_frame.rowconfigure(0, weight=1)
        logs_frame.columnconfigure(0, weight=1)
        
        self.console_text = scrolledtext.ScrolledText(
            logs_frame, wrap=tk.WORD,
            font=("Consolas", 10), bg="black", fg="lightgreen"
        )
        self.console_text.grid(row=0, column=0, sticky="nsew")
        
        # Tags para colorir output
        self.console_text.tag_config("INFO", foreground="lightblue")
        self.console_text.tag_config("ERROR", foreground="red")
        self.console_text.tag_config("SUCCESS", foreground="lightgreen")
        self.console_text.tag_config("DEBUG", foreground="yellow")
        
    def setup_console_redirect(self):
        """Redireciona print() para a UI"""
        self.old_stdout = sys.stdout
        sys.stdout = RedirectText(self.console_text, "INFO")
        
    def carregar_modelos(self):
        """Carrega a lista de modelos disponíveis"""
        try:
            if hasattr(self, 'status_var'):
                self.status_var.set("Carregando modelos...")
            print("🔍 Carregando modelos disponíveis...")
            modelos = obter_modelos_disponiveis()
            self.modelo_combo["values"] = modelos
            
            # Se o modelo atual não estiver na lista, selecionar o primeiro
            if self.modelo_var.get() not in modelos and modelos:
                self.modelo_var.set(modelos[0])
            elif not modelos:
                self.modelo_var.set("qwen/qwen2.5-vl-7b")  # Fallback
                
            print(f"✅ {len(modelos)} modelos carregados")
            if hasattr(self, 'status_var'):
                self.status_var.set(f"✅ {len(modelos)} modelos carregados")
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelos: {e}")
            if hasattr(self, 'status_var'):
                self.status_var.set("⚠️ Erro ao carregar modelos")
            # Fallback para lista padrão
            modelos_fallback = ["qwen/qwen2.5-vl-7b", "gpt-4-vision-preview"]
            self.modelo_combo["values"] = modelos_fallback
            self.modelo_var.set(modelos_fallback[0])
        
        # Resetar status após 3 segundos
        if hasattr(self, 'status_var') and hasattr(self, 'root'):
            self.root.after(3000, lambda: self.status_var.set("Aguardando..."))
    
    def atualizar_modelos(self):
        """Atualiza a lista de modelos"""
        self.carregar_modelos()
        
    def load_url_from_file(self):
        """Carrega URL de um arquivo de texto"""
        filename = filedialog.askopenfilename(
            title="Carregar URL",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    url = f.read().strip()
                    self.url_var.set(url)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo: {e}")
    
    def save_config(self):
        """Salva configuração atual"""
        filename = filedialog.asksaveasfilename(
            title="Salvar Configuração",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                config = f"""URL: {self.url_var.get()}
Max Passos: {self.max_passos_var.get()}
Modelo LLM: {self.modelo_var.get()}

Instruções:
{self.instructions_text.get("1.0", tk.END)}"""
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(config)
                messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")
    
    def clear_logs(self):
        """Limpa os logs da interface"""
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete("1.0", tk.END)
        self.console_text.config(state=tk.DISABLED)
        
    def start_agent(self):
        """Inicia o agente em thread separada"""
        if self.is_running:
            return
            
        # Validar inputs
        try:
            max_passos = int(self.max_passos_var.get())
            if max_passos <= 0:
                raise ValueError("Max passos deve ser maior que 0")
        except ValueError as e:
            messagebox.showerror("Erro", f"Max passos inválido: {e}")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Erro", "URL não pode estar vazia")
            return
            
        # Configurar UI
        self.is_running = True
        self.stop_requested = False  # Reset flag de parada
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        self.status_var.set("Executando...")
        
        # Pegar instruções customizadas
        instructions = self.instructions_text.get("1.0", tk.END).strip()
        modelo = self.modelo_var.get().strip()
        
        # Iniciar thread
        self.current_thread = threading.Thread(
            target=self.run_agent,
            args=(url, max_passos, instructions, modelo),
            daemon=True
        )
        self.current_thread.start()
        
    def run_agent(self, url, max_passos, instructions, modelo):
        """Executa o agente com instruções customizadas e modelo selecionado"""
        try:
            print(f"🚀 Iniciando agente com instruções customizadas...")
            print(f"📍 URL: {url}")
            print(f"🔢 Max passos: {max_passos}")
            print(f"🤖 Modelo LLM: {modelo}")
            print(f"🎯 Instruções: {instructions}")
            print("-" * 60)
            
            # Chama o agente passando instruções e modelo
            agente_explorador(url, max_passos, instructions, modelo)
            print("✅ Navegação concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            
        finally:
            # Restaurar UI
            self.root.after(0, self.agent_finished)
            
    def stop_agent(self):
        """Para o agente definindo flag de parada"""
        self.stop_requested = True
        self.status_var.set("Parando...")
        print("⏹️ Solicitação de parada enviada... aguardando fim do passo atual")
        
    def is_stop_requested(self):
        """Verifica se foi solicitada a parada"""
        return self.stop_requested
        
    def agent_finished(self):
        """Chamado quando o agente termina"""
        self.is_running = False
        self.stop_requested = False  # Reset flag
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        if self.status_var.get() == "Parando...":
            self.status_var.set("Parado pelo usuário")
        else:
            self.status_var.set("Concluído")
        
    def on_closing(self):
        """Chamado quando a janela é fechada"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "O agente ainda está rodando. Deseja sair mesmo assim?"):
                sys.stdout = self.old_stdout  # Restaurar stdout
                self.root.destroy()
        else:
            sys.stdout = self.old_stdout  # Restaurar stdout
            self.root.destroy()

def main():
    root = tk.Tk()
    app = AgenteUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
