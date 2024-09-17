echo "Восстанавливаю предметы..."
docker exec -i craftbot-mongo sh -c 'mongorestore --archive' < db_dump/items.dump

echo "Восстанавливаю сеты..."
docker exec -i craftbot-mongo sh -c 'mongorestore --archive' < db_dump/sets.dump

echo "Восстанавливаю тиры..."
docker exec -i craftbot-mongo sh -c 'mongorestore --archive' < db_dump/tier_type.dump

echo "Восстанавливаю рецепты..."
docker exec -i craftbot-mongo sh -c 'mongorestore --archive' < db_dump/blueprints.dump

echo "Восстановление завершено"
