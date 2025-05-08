# mm-algos
Bachelor's thesis project for analyzing different matchmaking algorithms with simulated data. 

### Setup:
- Clone repository locally.
- Create virtual environment on ``macOS``:
  ```
  python3 -m venv .venv
  ```

  On ``Windows``:
  ```
  python -m venv .venv
  ```

- Start virtual environment from ``bash`` or ``zsh`` or ``macOS`` terminal:
  ```
  source .venv/bin/activate
  ```

  On ``Windows`` ``cmd``:
  ```
  .venv\Scripts\activate.bash
  ```

- Check all the packages installed:
  ```
  pip list
  ```

- Save dependencies into ``requirements.txt``:
  ```
  pip freeze > requirements.txt
  ```

- Install all the dependencies from ``requirements.txt``:
  ```
  pip install -r requirements.txt
  ```
- Create ``MySQL`` container with the volume on docker for the database:
  ```
  docker-compose up -d
  ```
  Remember to have docker installed on your machine beforehand.
- To drop the container and volume, and start over, if something ain't working right, do:
  ```
  docker-compose down -v
  ```
  To just shut it down, do:
  ```
  docker-compose down
  ```
- To check what containers are active:
  ```
  docker ps
  ```
- To connect to your ``MySQL`` container:
  ```
  docker exec -it <container_name_or_id> mysql -u <MYSQL_USER> -p<MYSQL_PASSWORD>
  ```
  Replace ``container_name_or_id`` with the container id you can find with ``docker ps`` command and ``MYSQL_USER`` and ``MYSQL_PASSWORD`` with the ``docker-compose.yml`` environment data, or for the ``root`` user just use ``root`` and ``MYSQL_ROOT_PASSWORD``.
  
  After connecting to the container, you need to choose the database you want to work with. In our case it is ``matchmaking_db``, so you do this:
  ```
  \u matchmaking_db
  ```
  You can change the name to whatever you want in the ``docker-compose.yml``, just remember to also change it in the ``DATABASE_URL``.

- After that you can check the ``MySQL`` documentation to get the required SQL queries you want to execute. Add a ``DATABASE_URL`` in the ``.env`` file for your connection with the container:
  ```
  DATABASE_URL=mysql+mysqlconnector://user:password@127.0.0.1:3307/matchmaking_db?auth_plugin=mysql_native_password
  ```
  You can use any user name, password and port, just change it in the ``docker-compose.yml``.
  
  We need the auth_plugin query param, because for some reason it likes to check the passoword as ``caching_sha2_password`` instead of ``mysql_native_password``.

- To run the programm, do:
  ```
  python main.py
  ```

### Some useful SQL select queries:
  ```
  SELECT * FROM player_game_type_stats LIMIT 1;
  ```
  ```
  SELECT * FROM game_players WHERE player_id = 1 LIMIT 200;
  ```
  ```
  SELECT true_rating_after_game FROM game_players WHERE player_id = 1 LIMIT 600;
  ```
  ```
  SELECT * FROM game_players WHERE game_id IN (40, 41, 42);
  ```
  ```
  SELECT game_id FROM game_players WHERE player_id = 1 AND is_most_valuable_player = 1 LIMIT 100;
  ```
  ```
  SELECT game_id, is_most_valuable_player, is_least_valuable_player FROM game_players WHERE player_id = 1 LIMIT 100;
  ```
  ```
  SELECT game_id, is_most_valuable_player FROM game_players WHERE player_id = 1 LIMIT 100;
  ```
  ```
  SELECT * FROM player_game_type_stats WHERE true_rating < 300 AND player_id NOT IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40) AND game_type = 'TDM' LIMIT 20;
  ```
  ```
  WITH ref AS (
    SELECT
      true_rating AS ref_rating
    FROM
      player_game_type_stats
    WHERE
      player_id   = 1
      AND game_type = 'TDM'
  )

  SELECT
    p.*
  FROM
    player_game_type_stats AS p
    CROSS JOIN ref
  WHERE
    p.game_type = 'TDM'

    AND p.player_id NOT IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40)

    AND (
      p.last_time_played IS NULL
      OR p.last_time_played <= '2025-05-04 13:00:00'
    )

    AND p.true_rating BETWEEN ref.ref_rating - 300
                          AND ref.ref_rating + 300

  ORDER BY
    ABS(p.true_rating - ref.ref_rating) ASC

  LIMIT 11;
  ```