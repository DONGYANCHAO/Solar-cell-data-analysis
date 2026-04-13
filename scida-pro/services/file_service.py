# -*- coding: utf-8 -*-
import os
import ntpath
import pickle
import pandas as pd
from typing import Dict, List, Optional, Tuple
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FileExtensions, DataParameters, ConversionFactors
from logger import get_logger, FileReadError, FileSaveError, NonASCIIFilenameError, validate_ascii_filename


class FileService:
    def __init__(self, data_service):
        self.logger = get_logger('FileService')
        self.data_service = data_service
        self.previous_directory = ""
        
    def set_previous_directory(self, directory: str) -> None:
        self.previous_directory = directory
        
    def get_previous_directory(self) -> str:
        return self.previous_directory
    
    def load_data_files(self, file_paths: List[str]) -> Tuple[bool, bool, bool]:
        empty_data_warning = False
        non_ascii_warning = False
        read_error_warning = False
        
        for file_path in file_paths:
            if not validate_ascii_filename(file_path):
                non_ascii_warning = True
                continue
            
            self.previous_directory = ntpath.dirname(file_path)
            
            try:
                dataframe = self._read_file(file_path)
                if dataframe is None:
                    read_error_warning = True
                    continue
                    
                dataframe = self._process_dataframe(dataframe)
                
                if dataframe.empty:
                    empty_data_warning = True
                    continue
                
                dataframe = self.data_service.apply_conversion(dataframe)
                
                dataset_name = self._extract_dataset_name(file_path)
                dataframe.index.name = dataset_name
                
                dataset_id = self.data_service.get_next_dataset_id()
                self.data_service.add_dataset(dataset_id, dataframe)
                
            except Exception as e:
                self.logger.error(f"Error loading file {file_path}: {str(e)}")
                read_error_warning = True
        
        return empty_data_warning, non_ascii_warning, read_error_warning
    
    def _read_file(self, file_path: str) -> Optional[pd.DataFrame]:
        _, extension = ntpath.splitext(file_path)
        label_columns = self.data_service.get_label_columns()
        
        try:
            if extension.lower() == FileExtensions.CSV:
                try:
                    dataframe = pd.read_csv(file_path)[label_columns].dropna()
                except KeyError:
                    try:
                        dataframe = pd.read_csv(file_path, sep=';')[label_columns].dropna()
                    except KeyError:
                        return None
            else:
                try:
                    excel_data = pd.read_excel(file_path)
                    dataframe = excel_data[label_columns].dropna()
                except KeyError:
                    return None
                    
            return dataframe
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def _process_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        try:
            internal_columns = self.data_service.get_internal_columns()
            dataframe.columns = internal_columns
        except (KeyError, ValueError):
            return pd.DataFrame()
        
        dataframe = self.data_service.validate_and_clean_data(dataframe)
        return dataframe
    
    def _extract_dataset_name(self, file_path: str) -> str:
        base_name = ntpath.splitext(ntpath.basename(file_path))[0]
        return base_name[:ConversionFactors.DATASET_NAME_MAX_LENGTH - 1]
    
    def save_datasets_to_directory(
        self, 
        datasets: Dict[int, pd.DataFrame], 
        dest_dir: str,
        overwrite_callback=None
    ) -> bool:
        self.previous_directory = dest_dir
        yes_to_all = False
        
        for dataset_id in datasets:
            dataframe = datasets[dataset_id]
            filename = dataframe.index.name + FileExtensions.CSV
            save_path = self._build_save_path(dest_dir, filename)
            
            if os.path.isfile(save_path) and not yes_to_all:
                if overwrite_callback:
                    result = overwrite_callback(filename, dest_dir)
                    if result is None:
                        continue
                    elif result == 'cancel':
                        return False
                    elif result == 'yes_to_all':
                        yes_to_all = True
                    elif result == 'no':
                        save_path = result
                        if not save_path:
                            continue
            
            dataframe.to_csv(save_path, index=False)
        
        return True
    
    def _build_save_path(self, directory: str, filename: str) -> str:
        if os.name == 'nt':
            return directory + '\\' + filename
        return directory + '/' + filename
    
    def load_filter_settings(self, file_path: str) -> Optional[List[List]]:
        if not validate_ascii_filename(file_path):
            raise NonASCIIFilenameError(f"Non-ASCII filename: {file_path}")
        
        self.previous_directory = ntpath.dirname(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                filters = pickle.load(f)
            return filters
        except Exception as e:
            self.logger.error(f"Could not read filter settings: {str(e)}")
            raise FileReadError(f"Could not read file \"{ntpath.basename(file_path)}\"")
    
    def save_filter_settings(self, file_path: str, filters: List[List]) -> None:
        if not validate_ascii_filename(file_path):
            raise NonASCIIFilenameError(f"Non-ASCII filename: {file_path}")
        
        self.previous_directory = ntpath.dirname(file_path)
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(filters, f)
        except Exception as e:
            self.logger.error(f"Could not save filter settings: {str(e)}")
            raise FileSaveError(f"Could not save file \"{ntpath.basename(file_path)}\"")
    
    def load_custom_labels(self, file_path: str) -> Optional[List[str]]:
        if not validate_ascii_filename(file_path):
            raise NonASCIIFilenameError(f"Non-ASCII filename: {file_path}")
        
        self.previous_directory = ntpath.dirname(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                first_line = f.readline()
            
            first_line = first_line.decode("utf-8")
            first_line = "".join(first_line.split())
            labels = first_line.split(",")
            return labels
        except Exception as e:
            self.logger.error(f"Could not read custom labels: {str(e)}")
            raise FileReadError(f"Could not read file \"{ntpath.basename(file_path)}\"")
