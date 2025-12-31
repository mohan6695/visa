#!/usr/bin/env python3
"""
Simple HTTP server with MCP API endpoints for Supabase posts integration.
This serves as a bridge between the frontend and the MCP server.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import subprocess
import os

class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('stack-overflow-posts.html', 'r') as f:
                self.wfile.write(f.read().encode())
        elif self.path.endswith('.html'):
            try:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(self.path[1:], 'r') as f:
                    self.wfile.write(f.read().encode())
            except FileNotFoundError:
                self.send_error(404, 'File not found')
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path.startswith('/api/mcp/'):
            self.handle_mcp_request()
        else:
            self.send_error(404, 'Not Found')

    def handle_mcp_request(self):
        # Get the tool name from the path
        tool_name = self.path.split('/')[-1]
        
        # Get the request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            # Parse JSON data
            data = json.loads(post_data.decode())
            
            # Call the MCP server with the tool and data
            result = self.call_mcp_tool(tool_name, data)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_error(500, f'Internal Server Error: {str(e)}')

    def call_mcp_tool(self, tool_name, data):
        """
        Call the MCP server tool with the provided data.
        This is a simplified implementation that would need to be
        enhanced to properly communicate with the MCP server.
        """
        
        # For now, return mock data since we can't directly call the MCP server
        # In a real implementation, this would communicate with the MCP server
        
        if tool_name == 'get_posts':
            return {
                "posts": [
                    {
                        "id": 1,
                        "title": "H1B Cap Registration 2024 - Need Advice",
                        "content": "I'm planning to register for the H1B cap lottery this year. Can anyone share their experience with the process? What documents do I need to prepare?",
                        "author": {"name": "John Doe", "email": "john@example.com"},
                        "community": {"name": "H1B Discussion", "country": "USA"},
                        "like_count": 15,
                        "comment_count": 8,
                        "view_count": 120,
                        "tags": "h1b,cap,registration",
                        "created_at": "2024-12-20T10:30:00Z"
                    },
                    {
                        "id": 2,
                        "title": "F1 OPT STEM Extension Timeline",
                        "content": "Has anyone recently applied for STEM extension? What's the current processing time? I'm worried about my EAD card.",
                        "author": {"name": "Jane Smith", "email": "jane@example.com"},
                        "community": {"name": "F1 Students", "country": "USA"},
                        "like_count": 12,
                        "comment_count": 5,
                        "view_count": 89,
                        "tags": "f1,opt,stem",
                        "created_at": "2024-12-18T14:20:00Z"
                    },
                    {
                        "id": 3,
                        "title": "EB2 NIW Processing Time",
                        "content": "I filed my EB2 NIW application 6 months ago and still haven't received any response. Is this normal? Should I be concerned?",
                        "author": {"name": "Bob Johnson", "email": "bob@example.com"},
                        "community": {"name": "EB2 Discussion", "country": "USA"},
                        "like_count": 8,
                        "comment_count": 12,
                        "view_count": 156,
                        "tags": "eb2,niw,processing",
                        "created_at": "2024-12-15T09:15:00Z"
                    }
                ],
                "total": 3
            }
        
        elif tool_name == 'get_post_by_id':
            post_id = data.get('post_id', 1)
            return {
                "post": {
                    "id": post_id,
                    "title": "H1B Cap Registration 2024 - Need Advice",
                    "content": "I'm planning to register for the H1B cap lottery this year. Can anyone share their experience with the process? What documents do I need to prepare?",
                    "author": {"name": "John Doe", "email": "john@example.com"},
                    "community": {"name": "H1B Discussion", "country": "USA"},
                    "like_count": 15,
                    "comment_count": 8,
                    "view_count": 120,
                    "tags": "h1b,cap,registration",
                    "created_at": "2024-12-20T10:30:00Z"
                },
                "comments": [
                    {
                        "id": 1,
                        "post_id": post_id,
                        "author": {"name": "Jane Smith", "email": "jane@example.com"},
                        "content": "Make sure you have your degree certificates and transcripts ready. The registration process is quite straightforward.",
                        "created_at": "2024-12-20T12:45:00Z"
                    },
                    {
                        "id": 2,
                        "post_id": post_id,
                        "author": {"name": "Bob Johnson", "email": "bob@example.com"},
                        "content": "Don't forget to get your LCA from your employer before registration. It's crucial for the petition.",
                        "created_at": "2024-12-20T14:20:00Z"
                    },
                    {
                        "id": 3,
                        "post_id": post_id,
                        "author": {"name": "Alice Brown", "email": "alice@example.com"},
                        "content": "The processing time can vary significantly. I'd recommend preparing all documents in advance.",
                        "created_at": "2024-12-21T09:30:00Z"
                    }
                ]
            }
        
        elif tool_name == 'get_similar_posts':
            return {
                "similar_posts": [
                    {
                        "id": 2,
                        "title": "F1 OPT STEM Extension Timeline",
                        "content": "Has anyone recently applied for STEM extension? What's the current processing time? I'm worried about my EAD card.",
                        "author": {"name": "Jane Smith", "email": "jane@example.com"},
                        "community": {"name": "F1 Students", "country": "USA"},
                        "like_count": 12,
                        "comment_count": 5,
                        "view_count": 89,
                        "tags": "f1,opt,stem",
                        "created_at": "2024-12-18T14:20:00Z"
                    },
                    {
                        "id": 3,
                        "title": "EB2 NIW Processing Time",
                        "content": "I filed my EB2 NIW application 6 months ago and still haven't received any response. Is this normal? Should I be concerned?",
                        "author": {"name": "Bob Johnson", "email": "bob@example.com"},
                        "community": {"name": "EB2 Discussion", "country": "USA"},
                        "like_count": 8,
                        "comment_count": 12,
                        "view_count": 156,
                        "tags": "eb2,niw,processing",
                        "created_at": "2024-12-15T09:15:00Z"
                    }
                ],
                "total": 2
            }
        
        elif tool_name == 'vote_post':
            return {
                "success": True,
                "post_id": data.get('post_id'),
                "new_like_count": 16,
                "vote_type": data.get('vote_type')
            }
        
        elif tool_name == 'add_comment':
            return {
                "success": True,
                "comment": {
                    "id": 4,
                    "post_id": data.get('post_id'),
                    "author": {"name": "Demo User", "email": "demo@example.com"},
                    "content": data.get('content'),
                    "created_at": "2024-12-24T14:00:00Z"
                }
            }
        
        elif tool_name == 'get_popular_tags':
            return {
                "popular_tags": [
                    {"tag": "h1b", "count": 45},
                    {"tag": "f1", "count": 32},
                    {"tag": "eb2", "count": 28},
                    {"tag": "niw", "count": 25},
                    {"tag": "opt", "count": 22},
                    {"tag": "cap", "count": 18},
                    {"tag": "stem", "count": 15},
                    {"tag": "processing", "count": 12}
                ]
            }
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def log_message(self, format, *args):
        # Override to reduce log spam
        pass

def run_server(port=9000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHandler)
    print(f"Server running at http://localhost:{port}")
    print("Serving Stack Overflow style posts with MCP API endpoints")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()