import pandas as pd
import csv
import matplotlib.pyplot as plt
import matplotlib
import base64
from io import BytesIO

# Ensure Agg backend is used
matplotlib.use('Agg')

class CSVValidator:
    @staticmethod
    def validate_file(file):
        if not file:
            return False, "No file provided"
        if not file.filename.lower().endswith('.csv'):
            return False, "File must be a CSV file"
        try:
            stream = BytesIO(file.read())
            file.seek(0) 
            text_stream = stream.read().decode('utf-8').splitlines()
            if not text_stream:
                return False, "CSV file is empty"
            csv_reader = csv.reader(text_stream)
            headers = next(csv_reader)
            if not headers:
                return False, "CSV file has no headers"
            row_count = 0
            for row in csv_reader:
                row_count += 1
                if row_count > 0:
                    break
            if row_count == 0:
                return False, "CSV file has no data rows"
            return True, f"Valid CSV structure with {len(headers)} columns"
        except Exception as e:
            return False, f"Error reading CSV: {str(e)}"

class DataProcessor:
    def __init__(self, file):
        self.file = file
        self.data = None
        self.headers = None
        
    def load_data(self):
        try:
            self.data = pd.read_csv(self.file)
            self.headers = list(self.data.columns)
            return True, "Data loaded successfully"
        except Exception as e:
            return False, f"Error loading data: {str(e)}"
            
    def get_data_as_text(self):
        if self.data is None:
            return ""
        text_parts = []
        text_parts.append(f"Total Rows: {len(self.data)}")
        text_parts.append(f"Columns: {', '.join(self.headers)}")
        text_parts.append("\nFirst 10 rows:")
        text_parts.append(self.data.head(10).to_string())
        numeric_cols = self.data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            text_parts.append("\nSummary Statistics:")
            text_parts.append(self.data[numeric_cols].describe().to_string())
        return "\n".join(text_parts)

class DataVisualizer:
    def __init__(self, data_processor):
        self.processor = data_processor
        self.data = None
        self.cleaned_data = None
        self.numeric_columns = []
        
    def _detect_numeric_columns(self):
        if self.processor.data is None:
            return []
        self.data = self.processor.data
        numeric_cols = []
        for col in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[col]):
                numeric_cols.append(col)
            else:
                try:
                    pd.to_numeric(self.data[col], errors='raise')
                    numeric_cols.append(col)
                except (ValueError, TypeError):
                    continue
        exclude_patterns = ['id', 'index', 'year', 'month', 'day', 'hour', 'minute', 'second',
                           'timestamp', 'time', 'date', 'latitude', 'longitude', 'lat', 'lon', 'lng']
        filtered_cols = []
        for col in numeric_cols:
            col_lower = col.lower()
            if not any(pattern in col_lower for pattern in exclude_patterns):
                filtered_cols.append(col)
        return filtered_cols

    def clean_data(self):
        if self.processor.data is None:
            return False, "No data loaded"
        try:
            self.data = self.processor.data.copy()
            self.numeric_columns = self._detect_numeric_columns()
            if not self.numeric_columns:
                return False, "No numeric columns found for visualization"
            
            self.cleaned_data = self.data.copy()
            for col in self.numeric_columns:
                self.cleaned_data[col] = pd.to_numeric(self.cleaned_data[col], errors='coerce')
            self.cleaned_data = self.cleaned_data.dropna(subset=self.numeric_columns, how='all')
            
            if len(self.cleaned_data) == 0:
                return False, "No valid data after cleaning"
            return True, "Data cleaned successfully"
        except Exception as e:
            return False, f"Error cleaning data: {str(e)}"
            
    def _fig_to_base64(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight', facecolor='#0c0c0c', edgecolor='none')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return img_str

    def create_line_chart(self):
        if self.cleaned_data is None:
            return False, None

        columns_with_data = [col for col in self.numeric_columns if col in self.cleaned_data.columns and len(self.cleaned_data[col].dropna()) > 0]
        if not columns_with_data:
            return False, None
            
        fig = plt.figure(figsize=(10, 5))

        plt.rcParams['text.color'] = '#00ff41'
        plt.rcParams['axes.labelcolor'] = '#00ff41'
        plt.rcParams['xtick.color'] = '#00ff41'
        plt.rcParams['ytick.color'] = '#00ff41'
        plt.rcParams['axes.edgecolor'] = '#00ff41'
        fig.patch.set_facecolor('#0c0c0c')
        plt.gca().set_facecolor('#0c0c0c')
        
        colors = ['#00ff41', '#58a6ff', '#f1e05a', '#ea4aaa', '#b392f0']
        for idx, col in enumerate(columns_with_data[:5]): 
            data = self.cleaned_data[col].dropna()
            plt.plot(range(len(data)), data, marker='o', linewidth=2, markersize=3,
                    color=colors[idx % len(colors)], label=col, alpha=0.8)
                    
        plt.title('Air Quality Trend Over Time', fontsize=12, fontweight='bold', color='#00ff41')
        plt.xlabel('Time Period', fontsize=10)
        plt.ylabel('Value', fontsize=10)
        legend = plt.legend(loc='best', fontsize=8, facecolor='#0c0c0c', edgecolor='#00ff41')
        plt.grid(True, alpha=0.2, color='#00ff41')
        plt.tight_layout()
        
        return True, self._fig_to_base64(fig)

    def create_bar_chart(self):
        if self.cleaned_data is None:
            return False, None
        try:
            latest_values = {}
            for col in self.numeric_columns:
                if col in self.cleaned_data.columns:
                    valid_data = self.cleaned_data[col].dropna()
                    if len(valid_data) > 0:
                        latest_values[col] = valid_data.iloc[-1]
            if not latest_values:
                return False, None
                
            fig = plt.figure(figsize=(max(12, len(latest_values) * 1.2), 6))
            plt.rcParams['text.color'] = '#00ff41'
            plt.rcParams['axes.labelcolor'] = '#00ff41'
            plt.rcParams['xtick.color'] = '#00ff41'
            plt.rcParams['ytick.color'] = '#00ff41'
            plt.rcParams['axes.edgecolor'] = '#00ff41'
            fig.patch.set_facecolor('#0c0c0c')
            plt.gca().set_facecolor('#0c0c0c')
            
            colors = ['#ea4aaa', '#f1e05a', '#ff5555', '#62b7ec', '#00ff41', '#b392f0']
            bars = plt.bar(latest_values.keys(), latest_values.values(),
                          color=[colors[i % len(colors)] for i in range(len(latest_values))], alpha=0.8)
            plt.title('Current Air Quality Metrics Comparison', fontsize=12, fontweight='bold', color='#00ff41')
            plt.xlabel('Metric', fontsize=10)
            plt.ylabel('Value', fontsize=10)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.2, color='#00ff41', axis='y')
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=9, color='#00ff41')
            plt.tight_layout()
            return True, self._fig_to_base64(fig)
        except Exception as e:
            return False, None

    def create_histogram(self):
        if self.cleaned_data is None:
            return False, None
        try:
            columns_with_data = []
            for col in self.numeric_columns:
                if col in self.cleaned_data.columns and len(self.cleaned_data[col].dropna()) > 1:
                    columns_with_data.append(col)
            if not columns_with_data:
                return False, None
                
            num_plots = len(columns_with_data)
            if num_plots == 1:
                fig, axes = plt.subplots(1, 1, figsize=(10, 5))
                axes = [axes]
            elif num_plots == 2:
                fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                axes = axes.flatten()
            elif num_plots <= 4:
                fig, axes = plt.subplots(2, 2, figsize=(12, 8))
                axes = axes.flatten()
            elif num_plots <= 6:
                fig, axes = plt.subplots(2, 3, figsize=(14, 8))
                axes = axes.flatten()
            elif num_plots <= 9:
                fig, axes = plt.subplots(3, 3, figsize=(14, 10))
                axes = axes.flatten()
            else:
                rows = (num_plots + 2) // 3
                fig, axes = plt.subplots(rows, 3, figsize=(14, 4*rows))
                axes = axes.flatten()
                
            plt.rcParams['text.color'] = '#00ff41'
            plt.rcParams['axes.labelcolor'] = '#00ff41'
            plt.rcParams['xtick.color'] = '#00ff41'
            plt.rcParams['ytick.color'] = '#00ff41'
            plt.rcParams['axes.edgecolor'] = '#00ff41'
            fig.patch.set_facecolor('#0c0c0c')
            
            colors = ['#62b7ec', '#00ff41', '#ea4aaa', '#f1e05a', '#ff5555', '#b392f0']
            for idx, col in enumerate(columns_with_data):
                data = self.cleaned_data[col].dropna()
                ax = axes[idx]
                ax.set_facecolor('#0c0c0c')
                ax.hist(data, bins=min(20, max(5, len(data)//3)), color=colors[idx % len(colors)],
                       edgecolor='#0c0c0c', alpha=0.8)
                ax.set_title(f'{col} Distribution', fontsize=10, fontweight='bold', color='#00ff41')
                ax.set_xlabel(f'{col} Value Range', fontsize=8)
                ax.set_ylabel('Frequency', fontsize=8)
                ax.grid(True, alpha=0.2, color='#00ff41', axis='y')
                mean_val = data.mean()
                median_val = data.median()
                ax.axvline(x=mean_val, color='#ff5555', linestyle='--', linewidth=1.5,
                          label=f'Mean: {mean_val:.1f}')
                ax.axvline(x=median_val, color='#58a6ff', linestyle='--', linewidth=1.5,
                          label=f'Median: {median_val:.1f}')
                ax.legend(fontsize=7, facecolor='#0c0c0c', edgecolor='#00ff41')
                
            for idx in range(num_plots, len(axes)):
                fig.delaxes(axes[idx])
                
            plt.suptitle('Air Quality Data Distribution Analysis', fontsize=12, fontweight='bold', y=0.995, color='#00ff41')
            plt.tight_layout()
            return True, self._fig_to_base64(fig)
        except Exception as e:
            return False, None

    def generate_visualizations(self):
        clean_success, msg = self.clean_data()
        if not clean_success:
            return False, {}, msg
            
        charts = {}
        l_success, l_img = self.create_line_chart()
        if l_success: charts['line_chart'] = l_img
            
        b_success, b_img = self.create_bar_chart()
        if b_success: charts['bar_chart'] = b_img
            
        h_success, h_img = self.create_histogram()
        if h_success: charts['histogram'] = h_img
            
        return True, charts, "Visualizations generated"
