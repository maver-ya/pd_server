import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import psycopg2


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/tasks':
            self.get_tasks()
        elif self.path.startswith('/tasks/'):
            self.get_task(self.path.split('/')[-1])

    def do_POST(self):
        if self.path == '/tasks':
            self.add_task()

    def do_PUT(self):
        if self.path == '/tasks':
            self.update_task()

    def do_DELETE(self):
        if self.path.startswith('/tasks/'):
            self.delete_task(self.path.split('/')[-1])

    def connect_db(self):
        return psycopg2.connect(dbname='tasks', user='postgres', password='admin', host='localhost')

    def get_tasks(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks;")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(tasks).encode())

    def get_task(self, task_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
        task = cursor.fetchone()
        cursor.close()
        conn.close()

        if task:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(task).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def add_task(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        task_data = json.loads(post_data)

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, status) VALUES (%s, %s) RETURNING id;",
                       (task_data['title'], task_data['status']))
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'id': task_id}).encode())

    def update_task(self):
        content_length = int(self.headers['Content-Length'])
        put_data = self.rfile.read(content_length)
        task_data = json.loads(put_data)

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = %s WHERE id = %s;",
                       (task_data['status'], task_data['id']))
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(200)
        self.end_headers()

    def delete_task(self, task_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
        conn.commit()
        cursor.close()
        conn.close()

        self.send_response(204)
        self.end_headers()


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()


if __name__ == "__main__":
    run()