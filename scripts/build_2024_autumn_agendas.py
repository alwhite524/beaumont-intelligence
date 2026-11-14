"""Publish the five source-audited October–December 2024 Council packets."""
from build_2025_spring_agendas import build

DATES=['2024-10-01','2024-10-15','2024-11-19','2024-12-03','2024-12-17']

if __name__=='__main__':
    build(DATES,'October–December 2024 interactive agendas','autumn-2024-agendas','BI_AUTUMN')
