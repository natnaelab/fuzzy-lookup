import pandas as pd
from string_grouper import match_strings
import time
from pathlib import Path
from typing import Dict
from datetime import datetime
from pydantic import BaseModel
from ..models import User, UserFile, FuzzyJob
from .file import FileService


class FuzzyLookupRequest(BaseModel):
    file_name_1: str
    file_name_2: str
    file_1_column: str
    file_2_column: str
    threshold: float
    delimiter: str = ","
    output_type: str = "csv"


class SingleFileFuzzyRequest(BaseModel):
    filename: str
    column_1: str
    column_2: str
    threshold: float


class ColumnNamesResponse(BaseModel):
    filename: str
    column_names: Dict[str, str]


class OutputDataframe:
    def __init__(self, input_file: str):
        extension = Path(input_file).suffix.lower()
        if extension in [".csv", ".xlsx", ".xls"]:
            self.input_file = input_file
            self.extension = extension
        else:
            raise ValueError("Incorrect File Type. Supported types: csv, xlsx, xls")

    def convert_to_dataframe(self) -> pd.DataFrame:
        if self.extension == ".csv":
            # Try multiple encoding and delimiter combinations for CSV
            for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                for sep in [",", ";", "\t", "|"]:
                    try:
                        df = pd.read_csv(self.input_file, encoding=encoding, sep=sep, on_bad_lines='skip')
                        # Valid CSV should have at least 2 columns
                        if len(df.columns) > 1 and len(df) > 0:
                            return df
                    except Exception:
                        continue
            
            # If all combinations fail, try with default settings and error_bad_lines skip
            try:
                df = pd.read_csv(self.input_file, on_bad_lines='skip')
                if len(df) > 0:
                    return df
            except Exception as e:
                raise ValueError(f"Could not read CSV file. Please ensure the file is properly formatted. Error: {str(e)}")
            
            raise ValueError("Could not read CSV file with any encoding/delimiter combination")
        
        elif self.extension == ".xlsx":
            # Use openpyxl engine for .xlsx files (Excel 2007+)
            try:
                return pd.read_excel(self.input_file, engine="openpyxl", sheet_name=0)
            except Exception as e:
                raise ValueError(f"Could not read XLSX file. Error: {str(e)}")
        
        elif self.extension == ".xls":
            # Use xlrd engine for .xls files (Excel 97-2003)
            try:
                return pd.read_excel(self.input_file, engine="xlrd", sheet_name=0)
            except Exception as e:
                raise ValueError(f"Could not read XLS file. Please ensure xlrd is installed. Error: {str(e)}")


class FileProcessingHandler:
    def __init__(self, df: pd.DataFrame, threshold: float, processes: int = -1):
        self.df = df
        self.threshold = threshold
        self.processes = processes

    def pre_process_dataframe(self, column_1: str, column_2: str) -> pd.DataFrame:
        if column_1 not in self.df.columns or column_2 not in self.df.columns:
            raise ValueError(f"Columns {column_1} or {column_2} not found in dataframe")

        df_processed = self.df.copy()
        df_processed = df_processed.dropna(subset=[column_1, column_2])
        df_processed[column_1] = df_processed[column_1].astype(str).str.strip()
        df_processed[column_2] = df_processed[column_2].astype(str).str.strip()

        matches = match_strings(
            df_processed[column_1], df_processed[column_2], ignore_index=True, min_similarity=self.threshold
        )

        return pd.merge(matches, df_processed, left_on=f"left_{column_1}", right_on=column_1, how="inner")


class FuzzyLookupHelper:
    @staticmethod
    def fuzzy_lookup_preprocess(file_path: str, column_name: str) -> pd.DataFrame:
        try:
            output_df = OutputDataframe(file_path)
            df = output_df.convert_to_dataframe()

            df = df.dropna(subset=[column_name])
            df = df.astype(str)

            return df
        except Exception as e:
            raise

    @staticmethod
    def fuzzylookup_main(
        df1_processed: pd.DataFrame, df2_processed: pd.DataFrame, df1_col: str, df2_col: str, threshold: float
    ) -> pd.DataFrame:
        try:
            matches = match_strings(
                df1_processed[df1_col], df2_processed[df2_col], ignore_index=True, min_similarity=threshold
            )
            return matches
        except Exception as e:
            raise

    @staticmethod
    def fuzzylookup_postprocess(
        matches: pd.DataFrame,
        df1_processed: pd.DataFrame,
        df2_processed: pd.DataFrame,
        df1_col: str,
        df2_col: str,
        join_method: str = "inner",
    ) -> pd.DataFrame:
        try:
            data_final = pd.merge(matches, df1_processed, how=join_method, left_on=f"left_{df1_col}", right_on=df1_col)

            data_final = data_final[data_final.columns.drop(list(data_final.filter(regex="key")))]

            data_final2 = pd.merge(
                data_final, df2_processed, how=join_method, left_on=f"right_{df2_col}", right_on=df2_col
            )

            data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex="left_")))]
            data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex="right_")))]
            data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex="key_0")))]

            cols = [col for col in data_final2.columns if col != "similarity"] + ["similarity"]
            data_final2 = data_final2[cols]

            return data_final2
        except Exception as e:
            raise


class FuzzyService:
    def __init__(self, file_service: FileService = None):
        self.file_service = file_service or FileService()
        self.download_dir = Path("data/downloads")
        self.download_dir.mkdir(exist_ok=True)

    def get_column_names(self, file_path: str) -> Dict[str, str]:
        output_df = OutputDataframe(file_path)
        df = output_df.convert_to_dataframe()
        return {column_name: column_name for column_name in df.columns}

    def process_single_file_fuzzy_lookup(self, request: SingleFileFuzzyRequest, user: User, db) -> str:
        try:
            user_file = (
                db.query(UserFile)
                .filter(UserFile.user_id == user.id, UserFile.stored_filename == request.filename)
                .first()
            )

            if not user_file:
                raise FileNotFoundError("File not found")

            job = FuzzyJob(
                user_id=user.id,
                file_id=user_file.id,
                job_type="single_file",
                status="processing",
                file_1_column=request.column_1,
                file_2_column=request.column_2,
                threshold=request.threshold,
                started_at=datetime.utcnow(),
            )
            db.add(job)
            db.flush()

            output_df = OutputDataframe(user_file.file_path)
            df = output_df.convert_to_dataframe()

            file_processor = FileProcessingHandler(df, request.threshold)
            processed_df = file_processor.pre_process_dataframe(request.column_1, request.column_2)

            filename_parts = user_file.original_filename.rsplit(".", 1)
            if len(filename_parts) == 2:
                name, ext = filename_parts
                output_filename = f"processed_{name}_{time.strftime('%Y%m%d_%H%M%S')}.{ext}"
            else:
                output_filename = f"processed_{user_file.original_filename}_{time.strftime('%Y%m%d_%H%M%S')}"
            
            output_path = self.download_dir / output_filename

            processed_df.to_csv(output_path, index=False)

            job.status = "completed"
            job.output_filename = output_filename
            job.output_path = str(output_path)
            job.matches_count = len(processed_df)
            job.completed_at = datetime.utcnow()

            db.commit()

            return str(output_path)

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            raise

    def process_multi_file_fuzzy_lookup(self, request: FuzzyLookupRequest, user: User, db) -> str:
        try:
            user_file_1 = (
                db.query(UserFile)
                .filter(UserFile.user_id == user.id, UserFile.stored_filename == request.file_name_1)
                .first()
            )

            user_file_2 = (
                db.query(UserFile)
                .filter(UserFile.user_id == user.id, UserFile.stored_filename == request.file_name_2)
                .first()
            )

            if not user_file_1:
                raise FileNotFoundError(f"File {request.file_name_1} not found")
            if not user_file_2:
                raise FileNotFoundError(f"File {request.file_name_2} not found")

            job = FuzzyJob(
                user_id=user.id,
                file_1_id=user_file_1.id,
                file_2_id=user_file_2.id,
                job_type="multi_file",
                status="processing",
                file_1_column=request.file_1_column,
                file_2_column=request.file_2_column,
                threshold=request.threshold,
                delimiter=request.delimiter,
                output_type=request.output_type,
                started_at=datetime.utcnow(),
            )
            db.add(job)
            db.flush()

            df1_processed = FuzzyLookupHelper.fuzzy_lookup_preprocess(user_file_1.file_path, request.file_1_column)
            df2_processed = FuzzyLookupHelper.fuzzy_lookup_preprocess(user_file_2.file_path, request.file_2_column)

            matches = FuzzyLookupHelper.fuzzylookup_main(
                df1_processed, df2_processed, request.file_1_column, request.file_2_column, request.threshold
            )

            result_df = FuzzyLookupHelper.fuzzylookup_postprocess(
                matches, df1_processed, df2_processed, 
                request.file_1_column, request.file_2_column, "inner"
            )

            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_filename = f"fuzzy_match_{user_file_1.original_filename.split('.')[0]}_{user_file_2.original_filename.split('.')[0]}_{timestamp}.{request.output_type}"
            output_path = self.download_dir / output_filename

            if request.output_type == "xlsx":
                result_df.to_excel(output_path, index=False)
            else:
                delimiter = "\t" if len(request.delimiter) > 1 else request.delimiter
                result_df.to_csv(output_path, sep=delimiter, index=False)

            job.status = "completed"
            job.output_filename = output_filename
            job.output_path = str(output_path)
            job.matches_count = len(result_df)
            job.completed_at = datetime.utcnow()

            db.commit()

            return str(output_path)

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            raise
