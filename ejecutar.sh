#!/bin/bash
# Script de ejecución diaria vía cron.
# Ejecuta el scraping en modo consola y exporta resultados.
# Ejemplo crontab (cada día a las 8:00 AM):
# 0 8 * * * /home/tuusuario/buscatrabajo/ejecutar.sh

set -e

cd "$(dirname "$0")"
source venv/bin/activate

python main.py --cli --exportar data/ofertas_relevantes.csv
