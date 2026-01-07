#!/usr/bin/env python3
"""
Bind - Mac用デスクトップアプリ
フォルダ内のJPEG画像を順番通りに1つのPDFにまとめる
"""

import os
import sys
import re
import subprocess
import threading
import traceback
from pathlib import Path
from typing import List, Tuple, Optional
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import img2pdf
from pypdf import PdfWriter

# CustomTkinterの設定
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class BindApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bind")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.selected_folder = None
        self.image_files = []
        self.is_processing = False
        self.last_output_pdf: Optional[Path] = None
        
        self.setup_ui()
        # 起動時に初期状態を設定
        self.reset_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        # メインフレーム
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # タイトル
        title_label = ctk.CTkLabel(
            main_frame,
            text="Bind",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 30))
        
        # ドロップ領域（通常のtkinter Frameを使用して確実に動作）
        drop_container = ctk.CTkFrame(
            main_frame,
            width=500,
            height=200,
            fg_color="transparent"
        )
        drop_container.pack(pady=(0, 20))
        drop_container.pack_propagate(False)
        
        self.drop_frame = tk.Frame(
            drop_container,
            width=500,
            height=200,
            bg="#f5f5f5",
            relief="flat",
            highlightthickness=2,
            highlightbackground="#e0e0e0"
        )
        self.drop_frame.pack(fill="both", expand=True)
        self.drop_frame.pack_propagate(False)
        
        # ドロップ領域内のラベル（複数行表示用）
        self.drop_label_frame = tk.Frame(self.drop_frame, bg="#f5f5f5")
        self.drop_label_frame.pack(expand=True)
        
        self.drop_label = tk.Label(
            self.drop_label_frame,
            text="Drop a folder",
            font=("Helvetica", 16),
            fg="#666666",
            bg="#f5f5f5"
        )
        self.drop_label.pack()
        
        self.drop_info_label = tk.Label(
            self.drop_label_frame,
            text="",
            font=("Helvetica", 12),
            fg="#999999",
            bg="#f5f5f5"
        )
        self.drop_info_label.pack(pady=(5, 0))
        
        # ドラッグ&ドロップ設定
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        # 状態表示（フォルダ名と画像枚数）
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=12),
            text_color="#999999",
            wraplength=500
        )
        self.status_label.pack(pady=(0, 20))
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 20))
        
        # Select Folder ボタン
        select_btn = ctk.CTkButton(
            button_frame,
            text="Select Folder",
            command=self.select_folder,
            width=150,
            height=40,
            corner_radius=8
        )
        select_btn.pack(side="left", padx=10)
        
        # Create PDF ボタン
        self.create_btn = ctk.CTkButton(
            button_frame,
            text="Create PDF",
            command=self.create_pdf,
            width=150,
            height=40,
            corner_radius=8,
            state="disabled"
        )
        self.create_btn.pack(side="left", padx=10)
        
        # Open PDF ボタン（成功後に表示）
        self.open_btn = ctk.CTkButton(
            button_frame,
            text="Open PDF",
            command=self.open_pdf,
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#4caf50",
            hover_color="#45a049"
        )
        # 初期状態では非表示
        self.open_btn.pack_forget()
        
        # Reset ボタン
        self.reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset",
            command=self.reset_ui,
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#757575",
            hover_color="#616161",
            state="disabled"
        )
        # 初期状態では非表示（Open PDFと一緒に表示）
        self.reset_btn.pack_forget()
        
        # 進捗テキスト
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        )
        self.progress_label.pack(pady=(0, 10))
        
        # プログレスバー
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            width=500,
            height=20,
            corner_radius=10
        )
        self.progress_bar.pack()
        self.progress_bar.set(0)
        
    def set_folder(self, folder: Path):
        """フォルダを設定してUIを更新"""
        if not folder.is_dir():
            messagebox.showerror("Error", "Please select a folder, not a file.")
            return
        
        self.selected_folder = folder
        self.image_files = self.get_image_files(folder)
        self.last_output_pdf = None  # リセット
        
        # Dropゾーンの見た目を変更
        self.drop_frame.configure(
            bg="#e8f5e9",
            highlightbackground="#4caf50",
            highlightthickness=2
        )
        self.drop_label_frame.configure(bg="#e8f5e9")
        self.drop_label.configure(
            text=f"Selected: {folder.name}",
            fg="#2e7d32",
            bg="#e8f5e9",
            font=("Helvetica", 16)
        )
        
        # 画像枚数を表示
        image_count = len(self.image_files)
        if image_count == 0:
            self.drop_info_label.configure(
                text="No JPG/JPEG found",
                fg="#999999",
                bg="#e8f5e9"
            )
            self.status_label.configure(
                text="No folder selected",
                text_color="#999999"
            )
            self.create_btn.configure(state="disabled")
        else:
            image_text = f"{image_count} image{'s' if image_count != 1 else ''}"
            self.drop_info_label.configure(
                text=image_text,
                fg="#2e7d32",
                bg="#e8f5e9"
            )
            self.status_label.configure(
                text="Ready to create PDF",
                text_color="#333333"
            )
            self.create_btn.configure(state="normal")
        
        # Open PDFとResetボタンを非表示、Create PDFボタンを表示
        self.open_btn.pack_forget()
        self.reset_btn.pack_forget()
        self.create_btn.pack(side="left", padx=10)
    
    def reset_ui(self):
        """UIを完全に初期状態にリセット"""
        # 状態変数をリセット
        self.selected_folder = None
        self.image_files = []
        self.last_output_pdf = None
        self.is_processing = False
        
        # Dropゾーンの見た目をリセット
        self.drop_frame.configure(
            bg="#f5f5f5",
            highlightbackground="#e0e0e0",
            highlightthickness=2
        )
        self.drop_label_frame.configure(bg="#f5f5f5")
        self.drop_label.configure(
            text="Drop a folder",
            fg="#666666",
            bg="#f5f5f5",
            font=("Helvetica", 16)
        )
        self.drop_info_label.configure(
            text="",
            bg="#f5f5f5"
        )
        
        # 状態表示をリセット
        self.status_label.configure(
            text="No folder selected",
            text_color="#999999"
        )
        
        # 進捗表示をリセット
        self.progress_label.configure(text="")
        self.progress_bar.set(0)
        
        # ボタンの状態をリセット
        self.create_btn.configure(text="Create PDF", state="disabled")
        self.open_btn.configure(state="disabled")
        self.reset_btn.configure(state="disabled")
        
        # Open PDFとResetボタンを非表示、Create PDFボタンを表示
        self.open_btn.pack_forget()
        self.reset_btn.pack_forget()
        self.create_btn.pack(side="left", padx=10)
    
    def reset_folder_state(self):
        """フォルダ選択状態をリセット（後方互換性のため残す）"""
        self.reset_ui()
    
    def open_pdf(self):
        """PDFを開く（macOS）"""
        if self.last_output_pdf and self.last_output_pdf.exists():
            try:
                subprocess.run(["open", str(self.last_output_pdf)], check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF:\n{str(e)}")
    
    def on_drop(self, event):
        """ドロップイベント処理"""
        path = event.data.strip()
        # {} で囲まれる場合の処理
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        
        path_obj = Path(path)
        if path_obj.is_dir():
            self.set_folder(path_obj)
        else:
            messagebox.showerror("Error", "Please drop a folder, not a file.")
    
    def select_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.set_folder(Path(folder))
    
    def natural_sort_key(self, filename: str) -> Tuple[List[int], str]:
        """
        自然順ソート用のキー生成
        数字列を抽出して比較、数字がない場合は後ろに
        """
        # 数字列をすべて抽出
        numbers = [int(m) for m in re.findall(r'\d+', filename)]
        
        if not numbers:
            # 数字がない場合は後ろに回す（大きな値 + ファイル名）
            return ([999999], filename.lower())
        
        # 数字列とファイル名（小文字）を返す
        return (numbers, filename.lower())
    
    def get_image_files(self, folder: Path) -> List[Path]:
        """フォルダ内のJPEG画像ファイルを取得してソート"""
        image_extensions = {'.jpg', '.jpeg', '.JPG', '.JPEG'}
        image_files = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix in image_extensions
        ]
        
        # 自然順ソート
        image_files.sort(key=lambda f: self.natural_sort_key(f.name))
        
        return image_files
    
    def next_available_pdf_path(self, output_dir: Path, base_name: str) -> Path:
        """連番ファイル名を生成（既存ファイルがある場合は連番を付ける）"""
        base_path = output_dir / f"{base_name}.pdf"
        
        # 最初のファイルが存在しない場合はそのまま返す
        if not base_path.exists():
            return base_path
        
        # 連番を付けて存在しないファイル名を見つける
        counter = 2
        while True:
            numbered_path = output_dir / f"{base_name} ({counter}).pdf"
            if not numbered_path.exists():
                return numbered_path
            counter += 1
    
    def update_progress(self, current: int, total: int):
        """進捗表示を更新"""
        self.progress_label.configure(text=f"{current} / {total}")
        self.progress_bar.set(current / total if total > 0 else 0)
        self.root.update_idletasks()
    
    def create_pdf_async(self):
        """PDF作成処理（非同期）"""
        output_path = None
        try:
            if not self.selected_folder or not self.selected_folder.is_dir():
                messagebox.showerror("Error", "Please select a folder first.")
                return
            
            # 画像ファイルは既に取得済み（set_folderで取得）
            image_files = self.image_files
            
            if not image_files:
                messagebox.showerror("Error", "No JPEG images found in the folder.")
                self.is_processing = False
                self.create_btn.configure(text="Create PDF", state="normal")
                self.status_label.configure(
                    text="Ready to create PDF",
                    text_color="#333333"
                )
                return
            
            total = len(image_files)
            self.update_progress(0, total)
            
            # 出力パスを毎回計算（キャッシュしない）
            output_dir = self.selected_folder.parent
            base_name = self.selected_folder.name
            output_path = self.next_available_pdf_path(output_dir, base_name)
            
            # デバッグ用出力
            print(f"OUT: {output_path}")
            
            # バッチ処理の閾値（350枚以上）
            BATCH_THRESHOLD = 350
            BATCH_SIZE = 300
            
            if total <= BATCH_THRESHOLD:
                # 一括変換（最速）
                self.update_progress(0, total)
                with open(output_path, "wb") as f:
                    f.write(img2pdf.convert([str(img) for img in image_files]))
                self.update_progress(total, total)
            else:
                # バッチ処理
                temp_pdfs = []
                batch_count = (total + BATCH_SIZE - 1) // BATCH_SIZE
                
                for batch_idx in range(batch_count):
                    start_idx = batch_idx * BATCH_SIZE
                    end_idx = min(start_idx + BATCH_SIZE, total)
                    batch = image_files[start_idx:end_idx]
                    temp_pdf = output_path.parent / f"temp_{batch_idx}.pdf"
                    
                    self.update_progress(start_idx, total)
                    with open(temp_pdf, "wb") as f:
                        f.write(img2pdf.convert([str(img) for img in batch]))
                    temp_pdfs.append(temp_pdf)
                
                # 結合
                self.update_progress(total - len(temp_pdfs), total)
                merger = PdfWriter()
                for temp_pdf in temp_pdfs:
                    merger.append(temp_pdf)
                
                with open(output_path, "wb") as f:
                    merger.write(f)
                
                # 一時ファイル削除
                for temp_pdf in temp_pdfs:
                    temp_pdf.unlink()
                
                self.update_progress(total, total)
            
            # デバッグ用出力
            print(f"CREATED: {output_path.exists()} size={output_path.stat().st_size if output_path.exists() else 0}")
            
            # 成功時のUI更新（成功後にのみlast_output_pdfを設定）
            self.last_output_pdf = output_path
            self.status_label.configure(
                text=f"Created: {output_path.name}",
                text_color="#2e7d32"
            )
            self.progress_bar.set(1.0)
            self.progress_label.configure(text=f"{total} / {total}")
            
            # Create PDFボタンを非表示、Open PDFとResetボタンを表示
            self.create_btn.pack_forget()
            self.open_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            self.open_btn.pack(side="left", padx=10)
            self.reset_btn.pack(side="left", padx=10)
            
            # 成功メッセージは表示しない（UIのステータスで十分）
            
        except Exception as e:
            # 例外発生時の処理
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            
            # コンソールに出力
            print("=" * 60, file=sys.stderr)
            print("Error occurred while creating PDF:", file=sys.stderr)
            print(traceback_str, file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            
            # run.logにも出力
            log_path = Path(__file__).parent / "run.log"
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write("=" * 60 + "\n")
                    f.write(f"Error occurred: {error_msg}\n")
                    f.write(traceback_str + "\n")
                    f.write("=" * 60 + "\n\n")
            except Exception as log_error:
                print(f"Failed to write to log file: {log_error}", file=sys.stderr)
            
            # 出力PDFが存在してサイズ>0なら成功扱い（ポップアップは出さない）
            if output_path and output_path.exists() and output_path.stat().st_size > 0:
                # 成功扱い（警告はステータス文言のみ）
                self.last_output_pdf = output_path
                self.status_label.configure(
                    text=f"Created: {output_path.name}",
                    text_color="#2e7d32"
                )
                self.progress_bar.set(1.0)
                if self.image_files:
                    self.progress_label.configure(text=f"{len(self.image_files)} / {len(self.image_files)}")
                
                # Create PDFボタンを非表示、Open PDFとResetボタンを表示
                self.create_btn.pack_forget()
                self.open_btn.configure(state="normal")
                self.reset_btn.configure(state="normal")
                self.open_btn.pack(side="left", padx=10)
                self.reset_btn.pack(side="left", padx=10)
                
                # ポップアップは表示しない（UIのステータスで十分）
            else:
                # エラーダイアログを表示（詳細メッセージ必須）
                if output_path:
                    output_info = f"\nOutput path: {output_path}"
                else:
                    output_info = ""
                messagebox.showerror(
                    "Error",
                    f"Failed to create PDF:\n{error_msg}{output_info}\n\n"
                    f"Check run.log for details."
                )
        finally:
            self.is_processing = False
            # エラー時のみCreate PDFボタンの状態を更新（成功時はOpen PDFボタンが表示される）
            if not (output_path and output_path.exists() and output_path.stat().st_size > 0):
                # エラー時：フォルダが選択されていて画像がある場合は再有効化
                if self.selected_folder and len(self.image_files) > 0:
                    self.create_btn.configure(text="Create PDF", state="normal")
                    self.status_label.configure(
                        text="Ready to create PDF",
                        text_color="#333333"
                    )
                else:
                    self.create_btn.configure(text="Create PDF", state="disabled")
                    self.status_label.configure(
                        text="No folder selected",
                        text_color="#999999"
                    )
    
    def create_pdf(self):
        """PDF作成ボタン処理"""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        # ボタンを「Binding…」に変更
        self.create_btn.configure(text="Binding…", state="disabled")
        
        # ステータスを更新
        self.status_label.configure(
            text="Creating PDF...",
            text_color="#666666"
        )
        
        # 非同期処理
        thread = threading.Thread(target=self.create_pdf_async, daemon=True)
        thread.start()


def main():
    root = TkinterDnD.Tk()
    app = BindApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
