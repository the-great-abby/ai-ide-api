smart-merge-backup:
	python3 ../smart_merge_backup.py $(BACKUP)

random-pirate-log:
	docker compose exec misc-scripts python3 /scripts/random_pirate_log_entry.py

random-pirate-log-session:
	docker compose exec misc-scripts python3 /scripts/random_pirate_log_entry.py --context session

random-pirate-log-files:
	docker compose exec misc-scripts python3 /scripts/random_pirate_log_entry.py --context files

random-pirate-log-context:
	docker compose exec misc-scripts python3 /scripts/random_pirate_log_entry.py --context both 