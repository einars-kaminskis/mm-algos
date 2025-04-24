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

- Start virtual environment from ``bash`` or ``macOS`` terminal:
  ```
  source .venv/Scripts/activate
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
  
  After that you can check the ``MySQL`` documentation to get the required SQL queries you want to execute.
- Add a ``DATABASE_URL`` in the ``.env`` file for your connection with the container:
  ```
  DATABASE_URL=mysql+mysqlconnector://user:password@127.0.0.1:3307/matchmaking_db?auth_plugin=mysql_native_password
  ```
  You can use any user name, password and port, just change it in the ``docker-compose.yml``.
  
  We need the auth_plugin query param, because for some reason it likes to check the passoword as ``caching_sha2_password`` instead of ``mysql_native_password``.