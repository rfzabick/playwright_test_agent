"""Generate instrumentation code to capture function calls at runtime."""

import logging

logger = logging.getLogger(__name__)


def generate_wrapper(function_name: str, library: str) -> str:
    """Generate a wrapper function that captures inputs/outputs.

    The wrapper logs executable test code to the console.

    Args:
        function_name: Name of the function to wrap
        library: The library name

    Returns:
        JavaScript code for the wrapper
    """
    return f"""
(function() {{
  const originalFn = {function_name};
  {function_name} = function(...args) {{
    const result = originalFn.apply(this, args);

    try {{
      const serializedArgs = args.map(arg => {{
        if (typeof arg === 'function') {{
          // Try to capture simple arrow functions
          const fnStr = arg.toString();
          if (fnStr.includes('=>') && !fnStr.includes('{{')) {{
            return fnStr;
          }}
          return '/* function: ' + (arg.name || 'anonymous') + ' */';
        }}
        return JSON.stringify(arg);
      }});

      const serializedResult = JSON.stringify(result);
      const argsStr = serializedArgs.join(', ');

      console.log('// Test captured from runtime:');
      console.log(`expect({function_name}(${{argsStr}})).toEqual(${{serializedResult}});`);
    }} catch (e) {{
      console.log('// Could not serialize call to {function_name}:', e.message);
    }}

    return result;
  }};
}})();
"""


def generate_instrumentation_script(
    library: str,
    function_names: list[str],
) -> str:
    """Generate a complete instrumentation script for multiple functions.

    Args:
        library: The library name
        function_names: List of function names to instrument

    Returns:
        JavaScript code that can be injected into a page
    """
    logger.info(f"Generating instrumentation for {len(function_names)} functions")

    wrappers = []
    for fn in function_names:
        wrappers.append(generate_wrapper(fn, library))

    header = f"""
// Instrumentation for {library}
// Paste this into your browser console or inject into your dev environment
// Then interact with your app - test code will be logged to the console

console.log('=== {library} Instrumentation Active ===');
console.log('Interact with your app. Test code will appear below.');
console.log('');
"""

    return header + "\n".join(wrappers)
