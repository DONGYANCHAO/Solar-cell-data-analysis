# -*- coding: utf-8 -*-
from typing import List, Optional
import pandas as pd

from DataService import DataService
from FilterService import FilterService
from logger_config import setup_logger, handle_exceptions

logger = setup_logger(__name__)


class ReportBuilder:
    def __init__(self, report_path: str) -> None:
        self.report_path = report_path
        self.summaries: List[pd.DataFrame] = []
        self.yield_losses: List[pd.DataFrame] = []
        self.correlations: List[pd.DataFrame] = []
        self.writer: Optional[pd.ExcelWriter] = None

    def add_summary(self, summary: pd.DataFrame) -> 'ReportBuilder':
        self.summaries.append(summary)
        return self

    def add_yield_loss(self, yield_loss: pd.DataFrame) -> 'ReportBuilder':
        self.yield_losses.append(yield_loss)
        return self

    def add_correlation(self, correlation: pd.DataFrame) -> 'ReportBuilder':
        self.correlations.append(correlation)
        return self

    @handle_exceptions()
    def build(self, translator) -> str:
        with pd.ExcelWriter(self.report_path, engine='xlsxwriter') as writer:
            if self.summaries:
                output = pd.concat(self.summaries)
                output.to_excel(writer, str(translator.tr('Summary')))
                logger.info("Added summary sheet with %d datasets", len(self.summaries))

            if self.yield_losses:
                output = pd.concat(self.yield_losses)
                output.to_excel(writer, str(translator.tr('Yield loss')))
                logger.info("Added yield loss sheet with %d datasets", len(self.yield_losses))

            if self.correlations:
                output = pd.concat(self.correlations)
                output.to_excel(writer, str(translator.tr('Correlation')))
                logger.info("Added correlation sheet with %d datasets", len(self.correlations))

        logger.info("Report generated successfully: %s", self.report_path)
        return self.report_path


class ReportGenerator:
    def __init__(self, data_service: DataService, filter_service: FilterService) -> None:
        self.data_service = data_service
        self.filter_service = filter_service
        self.yield_loss_data: List[pd.DataFrame] = []

    def generate_summary_tables(self) -> List[pd.DataFrame]:
        summaries = []
        for dataset_idx in sorted(self.data_service.datasets.keys()):
            summaries.append(self.data_service.calculate_summary(dataset_idx))
        return summaries

    def generate_correlation_tables(self) -> List[pd.DataFrame]:
        correlations = []
        for dataset_idx in sorted(self.data_service.datasets.keys()):
            if len(self.data_service.get_dataset(dataset_idx)) > 1:
                correlations.append(self.data_service.calculate_correlation(dataset_idx))
        return correlations

    def process_yield_loss_for_report(self) -> List[pd.DataFrame]:
        processed = []
        for dataset_idx, yield_loss in enumerate(self.yield_loss_data):
            dataset_name = self.data_service.get_dataset_name(dataset_idx)
            processed.append(FilterService.process_yield_loss(yield_loss, dataset_name))
        return processed

    @handle_exceptions()
    def create_report(self, report_path: str, parent_widget) -> Optional[str]:
        if not self.data_service.has_data():
            logger.warning("Cannot create report: no data loaded")
            return None

        builder = ReportBuilder(report_path)

        summaries = self.generate_summary_tables()
        for summary in summaries:
            builder.add_summary(summary)

        if self.yield_loss_data:
            processed_yl = self.process_yield_loss_for_report()
            for yld_loss in processed_yl:
                builder.add_yield_loss(yld_loss)

        correlations = self.generate_correlation_tables()
        for corr in correlations:
            builder.add_correlation(corr)

        return builder.build(parent_widget)

    def clear_yield_loss(self) -> None:
        self.yield_loss_data = []

    def add_yield_loss(self, yield_loss: pd.DataFrame) -> None:
        self.yield_loss_data.append(yield_loss)
