"""Entrada de linha de comando do extrator."""

import argparse
import logging

from packages.shared.config import get_settings
from packages.shared.database import create_extractor_engine

from apps.extractor.pipeline import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza deputados da Câmara dos Deputados")
    parser.add_argument("command", choices=["sync"])
    parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    summary = run_ingestion(create_extractor_engine(settings), settings)
    print(
        "Ingestão concluída: "
        f"recebidos={summary.received} inseridos={summary.inserted} "
        f"atualizados={summary.updated} rejeitados={summary.rejected}"
    )


if __name__ == "__main__":
    main()
