import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time

class SerialPortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("串口通信工具")
        self.root.geometry("800x600")
        
        # 串口对象初始化
        self.ser = None
        self.is_connected = False
        self.receive_thread = None
        self.running = False
        
        # 创建UI界面
        self.create_widgets()
        
        # 刷新可用串口列表
        self.refresh_serial_ports()
        
        # 窗口关闭时的处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # ========== 串口配置区域 ==========
        config_frame = ttk.LabelFrame(self.root, text="串口配置")
        config_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 串口选择
        ttk.Label(config_frame, text="串口:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 刷新串口按钮
        refresh_btn = ttk.Button(config_frame, text="刷新", command=self.refresh_serial_ports)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 波特率选择
        ttk.Label(config_frame, text="波特率:").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.baudrate_var = tk.StringVar(value="9600")
        baudrates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        self.baud_combo = ttk.Combobox(config_frame, textvariable=self.baudrate_var, values=baudrates, width=10)
        self.baud_combo.grid(row=0, column=4, padx=5, pady=5)
        
        # 数据位选择
        ttk.Label(config_frame, text="数据位:").grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.databits_var = tk.StringVar(value="8")
        databits = ["5", "6", "7", "8"]
        self.data_combo = ttk.Combobox(config_frame, textvariable=self.databits_var, values=databits, width=5)
        self.data_combo.grid(row=0, column=6, padx=5, pady=5)
        
        # 停止位选择
        ttk.Label(config_frame, text="停止位:").grid(row=0, column=7, padx=5, pady=5, sticky=tk.W)
        self.stopbits_var = tk.StringVar(value="1")
        stopbits = ["1", "1.5", "2"]
        self.stop_combo = ttk.Combobox(config_frame, textvariable=self.stopbits_var, values=stopbits, width=5)
        self.stop_combo.grid(row=0, column=8, padx=5, pady=5)
        
        # 校验位选择
        ttk.Label(config_frame, text="校验位:").grid(row=0, column=9, padx=5, pady=5, sticky=tk.W)
        self.parity_var = tk.StringVar(value="N")
        parity = ["N", "E", "O", "M", "S"]
        self.parity_combo = ttk.Combobox(config_frame, textvariable=self.parity_var, values=parity, width=5)
        self.parity_combo.grid(row=0, column=10, padx=5, pady=5)
        
        # 连接/断开按钮
        self.connect_btn = ttk.Button(config_frame, text="打开串口", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=11, padx=10, pady=5)
        
        # ========== 数据发送区域 ==========
        send_frame = ttk.LabelFrame(self.root, text="数据发送")
        send_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 发送输入框
        self.send_text = tk.Text(send_frame, height=5)
        self.send_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # 发送按钮
        send_btn = ttk.Button(send_frame, text="发送", command=self.send_data)
        send_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 清空发送框按钮
        clear_send_btn = ttk.Button(send_frame, text="清空", command=lambda: self.send_text.delete(1.0, tk.END))
        clear_send_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # ========== 数据接收区域 ==========
        receive_frame = ttk.LabelFrame(self.root, text="数据接收")
        receive_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # 接收显示框（带滚动条）
        self.receive_text = scrolledtext.ScrolledText(receive_frame, wrap=tk.WORD)
        self.receive_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 清空接收框按钮
        clear_receive_btn = ttk.Button(receive_frame, text="清空接收区", command=lambda: self.receive_text.delete(1.0, tk.END))
        clear_receive_btn.pack(side=tk.BOTTOM, padx=5, pady=5)

    def refresh_serial_ports(self):
        """刷新可用串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)

    def toggle_connection(self):
        """打开/关闭串口连接"""
        if not self.is_connected:
            # 打开串口
            try:
                port = self.port_var.get()
                baudrate = int(self.baudrate_var.get())
                databits = int(self.databits_var.get())
                stopbits = float(self.stopbits_var.get())
                parity = self.parity_var.get()
                
                # 转换停止位和校验位格式以适配pyserial
                stopbits_map = {1.0: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2.0: serial.STOPBITS_TWO}
                parity_map = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD,
                              'M': serial.PARITY_MARK, 'S': serial.PARITY_SPACE}
                
                self.ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=databits,
                    stopbits=stopbits_map[stopbits],
                    parity=parity_map[parity],
                    timeout=0.1
                )
                
                self.is_connected = True
                self.connect_btn.config(text="关闭串口")
                messagebox.showinfo("成功", f"已成功打开串口 {port}")
                
                # 启动接收线程
                self.running = True
                self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
                self.receive_thread.start()
                
            except Exception as e:
                messagebox.showerror("错误", f"打开串口失败: {str(e)}")
        else:
            # 关闭串口
            self.running = False
            time.sleep(0.1)  # 等待接收线程退出
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.is_connected = False
            self.connect_btn.config(text="打开串口")
            messagebox.showinfo("提示", "串口已关闭")

    def receive_data(self):
        """接收串口数据（在独立线程中运行）"""
        while self.running:
            if self.ser and self.ser.is_open:
                try:
                    # 读取可用数据
                    data = self.ser.read(self.ser.in_waiting or 1)
                    if data:
                        # 将字节数据转换为字符串显示
                        text = data.decode('utf-8', errors='replace')
                        # 在GUI中更新接收数据（线程安全）
                        self.root.after(0, self.update_receive_text, text)
                except Exception as e:
                    self.root.after(0, messagebox.showerror, "接收错误", f"数据接收失败: {str(e)}")
                    self.running = False
            time.sleep(0.01)

    def update_receive_text(self, text):
        """更新接收文本框（线程安全的GUI操作）"""
        self.receive_text.insert(tk.END, text)
        # 自动滚动到最后
        self.receive_text.see(tk.END)

    def send_data(self):
        """发送数据到串口"""
        if not self.is_connected:
            messagebox.showwarning("警告", "请先打开串口！")
            return
        
        # 获取发送框中的文本
        send_content = self.send_text.get(1.0, tk.END).strip()
        if not send_content:
            messagebox.showwarning("警告", "发送内容不能为空！")
            return
        
        try:
            # 将字符串转换为字节并发送
            self.ser.write(send_content.encode('utf-8'))
            # 可选：在接收区回显发送的内容
            self.update_receive_text(f"[发送] {send_content}\n")
        except Exception as e:
            messagebox.showerror("错误", f"发送数据失败: {str(e)}")

    def on_closing(self):
        """窗口关闭时的清理操作"""
        if self.is_connected:
            self.toggle_connection()
        self.root.destroy()

if __name__ == "__main__":
    # 安装依赖（如果未安装）
    try:
        import serial
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
        import serial
    
    # 创建主窗口并运行
    root = tk.Tk()
    app = SerialPortGUI(root)
    root.mainloop()