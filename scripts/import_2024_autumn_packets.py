"""Import the five supplied October–December 2024 Council packets."""
from import_2025_spring_packets import main

MEETINGS={
    '2024-10-01':('Oct01_2024','fe860a70-1cc2-4b39-b427-062f850c1b1e'),
    '2024-10-15':('Oct15_2024','db9d6c67-e500-4e06-9cb6-793e87af562f'),
    '2024-11-19':('Nov19_2024','75c14ac7-19f4-42d9-8594-fd8f8bc14c0c'),
    '2024-12-03':('Dec03_2024','e7b8d889-395c-428d-b21f-b780c4903db9'),
    '2024-12-17':('Dec17_2024','c91ce289-b131-4485-a14d-5791b82a74b5'),
}

if __name__=='__main__':
    main(MEETINGS,'2024-autumn')
