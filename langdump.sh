rm app/lang_data/sharesfor/*
mongodump --db=sharesfor --collection=labels --out=app/lang_data
mongodump --db=sharesfor --collection=exceptions --out=app/lang_data

