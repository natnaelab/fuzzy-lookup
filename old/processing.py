import pandas as pd
import psutil
from multiprocessing import Pool
from functools import partial
from string_grouper import group_similar_strings,match_strings
import Levenshtein


class FileProcessingHandler:
    """
    A class to handle file processing, grouping similar strings, and calculating similarity metrics.
    """

    def __init__(self, column_name, threshold, processes=-1):
        self.column_name = column_name
        self.threshold = threshold
        self.processes = processes

    def group_similar_strings_in_dataframe(self, df):
        """
        Group similar strings in a DataFrame based on a similarity threshold.
        """
        print(f"The threshold is {self.threshold}")
        grouped_df = group_similar_strings(df[self.column_name], min_similarity=self.threshold)
        df = df.merge(grouped_df, how='left', left_on=self.column_name, right_on='string')
        return df.reset_index(drop=True)

    def process_dataframe_chunks(self, df_split2):
        """
        Process DataFrame chunks in parallel to group similar strings.
        """
        # Decide the number of processes
        num_cpus = psutil.cpu_count(logical=False) if self.processes <= 0 else self.processes
        process_pool = Pool(processes=num_cpus)
        func = partial(self.group_similar_strings_in_dataframe)
        dfs = process_pool.map(func, df_split2)
        process_pool.close()
        process_pool.join()
        data = pd.concat(dfs, ignore_index=True)
        return data

    def calculate_similarity_metrics(self, dfs_combined):
        """
        Calculate similarity metrics for the grouped strings.
        """
        dfs_combined['Distance'] = dfs_combined.apply(
            lambda x: Levenshtein.distance(x[self.column_name], x['group rep']), axis=1)
        dfs_combined['Similarity'] = dfs_combined.apply(
            lambda x: Levenshtein.ratio(x[self.column_name], x['group rep']), axis=1)
        dfs_combined = dfs_combined[dfs_combined['Distance'] < 5]
        data_framerawgrouped1 = dfs_combined.groupby(['group rep ID', 'group rep']).size().reset_index(name='counts')
        data_framerawgrouped1 = data_framerawgrouped1[data_framerawgrouped1['counts'] > 1].reset_index(drop=True)
        data_framerawgrouped1 = data_framerawgrouped1.sort_values(by='group rep', ascending=True)
        data_framerawgrouped1['rank'] = data_framerawgrouped1.index + 1
        data_finalgroup = pd.merge(dfs_combined, data_framerawgrouped1, how='inner', on='group rep ID')
        data_finalgroup = data_finalgroup.sort_values(by='rank', ascending=True)
        data_finalgroup.insert(0, 'rank', data_finalgroup.pop('rank'))
        data_finalgroup.drop(['group rep_y'], axis=1, inplace=True)
        return data_finalgroup


class FuzzyLookupHelper:
    @staticmethod
    def fuzzy_lookup_preprocess(df, column_name):
        """
        Returns data frame that has been preprocessed for fuzzylookup

        :param df:
        :param subset_col:
        :return:
        """
        df = self.output_df.dropna(subset=[subset_col])
        df = df.astype(str)
        return df

    @staticmethod
    def fuzzylookup_main(df1_processed, df2_processed, df1_col, df2_col, threshold):
        """
        Uses `string_grouper.match_strings` to perform fuzzy lookup between two DataFrames.
        """
        # Perform fuzzy matching between the specified columns
        matches = match_strings(df1_processed[df1_col], df2_processed[df2_col], ignore_index=True, min_similarity=threshold)
        return matches

    @staticmethod
    def fuzzylookup_postprocess(matches, df1_processed, df2_processed, df1_col, df2_col, join_method):
        """
        Post-processes the matches by merging the results into a final DataFrame.
        """
        data_final = pd.merge(matches, df1_processed, how=join_method, left_on=matches[f'left_{df1_col}'], right_on=df1_processed[df1_col])
        data_final = data_final[data_final.columns.drop(list(data_final.filter(regex='key')))]
        data_final2 = pd.merge(data_final, df2_processed, how=join_method, left_on=data_final[f'right_{df2_col}'], right_on=df2_processed[df2_col])
        data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex='left_')))]
        data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex='right_')))]
        data_final2 = data_final2[data_final2.columns.drop(list(data_final2.filter(regex='key_0')))]
        data_final2 = data_final2[[col for col in data_final2.columns if col != 'similarity'] + ['similarity']]
        return data_final2

