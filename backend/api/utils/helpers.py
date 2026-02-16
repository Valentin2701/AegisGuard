import functools
import logging
import traceback
from datetime import datetime
from flask import jsonify, current_app, request
from werkzeug.exceptions import HTTPException
import redis
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API Exception with status code and details"""
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource_type, resource_id):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id}
        )

class ValidationError(APIError):
    """Input validation error"""
    def __init__(self, message, field=None):
        details = {'field': field} if field else {}
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )

class SimulationError(APIError):
    """Simulation-specific error"""
    def __init__(self, message, status_code=500):
        super().__init__(
            message=message,
            status_code=status_code
        )

class RedisConnectionError(APIError):
    """Redis connection error"""
    def __init__(self):
        super().__init__(
            message="Unable to connect to Redis. Please check if Redis server is running.",
            status_code=503,
            details={'service': 'redis'}
        )

def handle_errors(f):
    """
    Decorator to handle errors in Flask routes consistently.
    Provides:
    - Exception catching and logging
    - Appropriate HTTP status codes
    - Consistent error response format
    - Request logging
    - Performance tracking
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Start timing the request
        start_time = datetime.now()
        
        # Get request info for logging
        request_info = {
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else 'Unknown'
        }
        
        try:
            # Log the incoming request
            logger.info(f"Request started: {request.method} {request.path}")
            
            # Execute the route function
            response = f(*args, **kwargs)
            
            # Calculate request duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log successful request
            logger.info(
                f"Request completed: {request.method} {request.path} - "
                f"Status: 200 - Duration: {duration:.3f}s"
            )
            
            return response
            
        except NotFoundError as e:
            # Handle resource not found errors
            duration = (datetime.now() - start_time).total_seconds()
            logger.warning(
                f"Not Found: {request.method} {request.path} - "
                f"{e.message} - Duration: {duration:.3f}s"
            )
            return jsonify({
                'error': e.message,
                'error_type': 'not_found',
                'details': e.details,
                'status_code': e.status_code,
                'timestamp': datetime.now().isoformat()
            }), e.status_code
            
        except ValidationError as e:
            # Handle validation errors
            duration = (datetime.now() - start_time).total_seconds()
            logger.warning(
                f"Validation Error: {request.method} {request.path} - "
                f"{e.message} - Duration: {duration:.3f}s"
            )
            return jsonify({
                'error': e.message,
                'error_type': 'validation_error',
                'details': e.details,
                'status_code': e.status_code,
                'timestamp': datetime.now().isoformat()
            }), e.status_code
            
        except SimulationError as e:
            # Handle simulation-specific errors
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Simulation Error: {request.method} {request.path} - "
                f"{e.message} - Duration: {duration:.3f}s\n"
                f"{traceback.format_exc()}"
            )
            return jsonify({
                'error': e.message,
                'error_type': 'simulation_error',
                'status_code': e.status_code,
                'timestamp': datetime.now().isoformat()
            }), e.status_code
            
        except redis.ConnectionError as e:
            # Handle Redis connection errors
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Redis Connection Error: {request.method} {request.path} - "
                f"Duration: {duration:.3f}s\n"
                f"{traceback.format_exc()}"
            )
            return jsonify({
                'error': "Redis connection error. Please check if Redis is running.",
                'error_type': 'redis_error',
                'status_code': 503,
                'timestamp': datetime.now().isoformat()
            }), 503
            
        except pickle.PickleError as e:
            # Handle pickling errors (for network graph serialization)
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Pickling Error: {request.method} {request.path} - "
                f"Duration: {duration:.3f}s\n"
                f"{traceback.format_exc()}"
            )
            return jsonify({
                'error': "Error serializing network data",
                'error_type': 'serialization_error',
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }), 500
            
        except HTTPException as e:
            # Handle Werkzeug HTTP exceptions
            duration = (datetime.now() - start_time).total_seconds()
            logger.warning(
                f"HTTP Exception: {request.method} {request.path} - "
                f"{e.description} - Duration: {duration:.3f}s"
            )
            return jsonify({
                'error': e.description,
                'error_type': 'http_error',
                'status_code': e.code,
                'timestamp': datetime.now().isoformat()
            }), e.code
            
        except Exception as e:
            # Handle any other unexpected errors
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Unexpected Error: {request.method} {request.path} - "
                f"{str(e)} - Duration: {duration:.3f}s\n"
                f"{traceback.format_exc()}"
            )
            
            # In development, return the actual error
            if current_app.debug:
                return jsonify({
                    'error': str(e),
                    'error_type': 'internal_error',
                    'traceback': traceback.format_exc(),
                    'status_code': 500,
                    'timestamp': datetime.now().isoformat()
                }), 500
            
            # In production, return a generic message
            return jsonify({
                'error': "An internal server error occurred",
                'error_type': 'internal_error',
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }), 500
            
    return decorated_function

def validate_required_fields(data, required_fields):
    """
    Helper function to validate required fields in request data
    
    Args:
        data: The request data (dict)
        required_fields: List of required field names
    
    Returns:
        tuple: (is_valid, missing_fields)
    """
    if not data:
        return False, required_fields
    
    missing = [field for field in required_fields if field not in data]
    return len(missing) == 0, missing

def sanitize_input(data):
    """
    Sanitize input data to prevent injection attacks
    
    Args:
        data: Input data (can be string, dict, list)
    
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Remove any potentially dangerous characters
        import re
        # Basic sanitization - remove HTML tags and special characters
        data = re.sub(r'<[^>]*>', '', data)
        data = data.replace('"', '\\"').replace("'", "\\'")
        return data
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data

def create_success_response(message, data=None, status_code=200):
    """
    Create a standardized success response
    
    Args:
        message: Success message
        data: Optional data to include
        status_code: HTTP status code
    
    Returns:
        tuple: (json_response, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def create_error_response(message, error_type='error', details=None, status_code=400):
    """
    Create a standardized error response
    
    Args:
        message: Error message
        error_type: Type of error
        details: Additional error details
        status_code: HTTP status code
    
    Returns:
        tuple: (json_response, status_code)
    """
    response = {
        'success': False,
        'error': message,
        'error_type': error_type,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code

def paginate_results(items, page, per_page):
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        dict: Paginated results with metadata
    """
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': len(items),
        'total_pages': (len(items) + per_page - 1) // per_page
    }

def parse_int_param(value, default=None, min_value=None, max_value=None):
    """
    Safely parse an integer parameter from request
    
    Args:
        value: The value to parse
        default: Default value if parsing fails
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        int or default
    """
    try:
        result = int(value)
        if min_value is not None and result < min_value:
            return default
        if max_value is not None and result > max_value:
            return default
        return result
    except (ValueError, TypeError):
        return default