import subprocess
import tempfile
import os
import ast
import re

class ScriptExecutor:
    def __init__(self):
        pass

    def run_script(self, script_content):
        """Execute the script using python command"""
        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_file = f.name

            # Run the script
            result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=60)

            # Clean up
            os.unlink(temp_file)

            output = f"Exit code: {result.returncode}\n"
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"Errors:\n{result.stderr}"

            return output

        except subprocess.TimeoutExpired:
            return "Script execution timed out"
        except Exception as e:
            return f"Error executing script: {str(e)}"

    def estimate_time(self, script_content, pc_per_hour=5.2):
        """Advanced time estimation based on proton charge and time calculations"""
        try:
            # Parse the script into AST
            tree = ast.parse(script_content)
            
            # Analyze the AST for proton charge and time usage
            analyzer = ProtonChargeAnalyzer()
            analyzer.visit(tree)
            
            total_pc = analyzer.total_proton_charge
            total_time_seconds = analyzer.total_time_seconds
            
            # Convert PC to hours
            pc_hours = total_pc / pc_per_hour
            
            # Convert time seconds to hours
            time_hours = total_time_seconds / 3600.0
            
            # Total estimated hours
            estimated_hours = pc_hours + time_hours
            
            if estimated_hours > 0:
                # Show breakdown
                if total_pc > 0 and total_time_seconds > 0:
                    return f"{estimated_hours:.1f} hours ({total_pc:.1f} PC + {total_time_seconds:.0f}s)"
                elif total_pc > 0:
                    return f"{estimated_hours:.1f} hours ({total_pc:.1f} PC)"
                else:
                    return f"{estimated_hours:.1f} hours ({total_time_seconds:.0f} seconds)"
            else:
                # Fallback to basic estimation if no measurements found
                lines = len(script_content.split('\n'))
                functions = len(re.findall(r'def \w+', script_content))
                estimated_hours = (lines / 100) + (functions / 10) + 0.1
                estimated_pc = estimated_hours * pc_per_hour
                return f"{estimated_hours:.1f} hours ({estimated_pc:.1f} PC, estimated)"
                
        except Exception as e:
            # Fallback on error
            lines = len(script_content.split('\n'))
            functions = len(re.findall(r'def \w+', script_content))
            estimated_hours = (lines / 100) + (functions / 10) + 0.1
            estimated_pc = estimated_hours * pc_per_hour
            return f"{estimated_hours:.1f} hours ({estimated_pc:.1f} PC, basic estimate)"


class ProtonChargeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze proton charge and time usage in EQ-SANS scripts"""
    
    def __init__(self):
        self.total_proton_charge = 0.0
        self.total_time_seconds = 0.0  # Track time-based measurements
        self.loop_multiplier = 1
        self.loop_stack = []  # Stack to track nested loops
        self.variable_assignments = {}  # Track variable assignments for loop analysis

    def visit_Assign(self, node):
        """Track variable assignments, especially lists used in loops"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if isinstance(node.value, ast.List):
                    # Track list assignments like temp_list = [40, 50, 70]
                    self.variable_assignments[var_name] = len(node.value.elts)
                elif isinstance(node.value, ast.Num):
                    # Track numeric assignments
                    self.variable_assignments[var_name] = node.value.n
        self.generic_visit(node)
        
    def visit_For(self, node):
        """Handle for loops"""
        self.loop_stack.append('for')
        
        # Try to determine loop iterations
        iterations = self._estimate_loop_iterations(node)
        old_multiplier = self.loop_multiplier
        self.loop_multiplier *= iterations
        
        # Visit loop body
        self.generic_visit(node)
        
        # Restore multiplier
        self.loop_multiplier = old_multiplier
        self.loop_stack.pop()
        
    def visit_While(self, node):
        """Handle while loops - assume they run a few times"""
        self.loop_stack.append('while')
        
        old_multiplier = self.loop_multiplier
        self.loop_multiplier *= 3  # Conservative estimate for while loops
        
        self.generic_visit(node)
        
        self.loop_multiplier = old_multiplier
        self.loop_stack.pop()
        
    def visit_Call(self, node):
        """Handle function calls, especially runsampleid and delay"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            if func_name == 'runsampleid':
                # This is a runsampleid call
                if len(node.args) >= 6:  # runsampleid has 6 parameters
                    # Check the 4th argument for unit type ('pc' or 'time')
                    unit_arg = node.args[3]
                    if isinstance(unit_arg, ast.Str):
                        unit = unit_arg.s
                        value_arg = node.args[5]
                        measurement_value = self._extract_numeric_value(value_arg)
                        
                        if measurement_value > 0:
                            if unit == 'pc':
                                # Proton charge mode
                                self.total_proton_charge += measurement_value * self.loop_multiplier
                            elif unit == 'time':
                                # Time mode (seconds)
                                self.total_time_seconds += measurement_value * self.loop_multiplier
                                
            elif func_name == 'delay':
                # This is a delay call (time in seconds)
                if len(node.args) >= 1:
                    delay_value = self._extract_numeric_value(node.args[0])
                    if delay_value > 0:
                        self.total_time_seconds += delay_value * self.loop_multiplier
                        
        self.generic_visit(node)
        
    def _estimate_loop_iterations(self, for_node):
        """Estimate number of iterations for a for loop"""
        if isinstance(for_node.iter, ast.List):
            # for item in [1, 2, 3, ...]
            return len(for_node.iter.elts)
        elif isinstance(for_node.iter, ast.Call):
            # for item in range(...) or len(...)
            if isinstance(for_node.iter.func, ast.Name):
                if for_node.iter.func.id == 'range':
                    if len(for_node.iter.args) == 1:
                        # range(n) -> n iterations
                        return self._extract_numeric_value(for_node.iter.args[0])
                    elif len(for_node.iter.args) == 2:
                        # range(start, end) -> end - start iterations
                        start = self._extract_numeric_value(for_node.iter.args[0]) or 0
                        end = self._extract_numeric_value(for_node.iter.args[1])
                        return max(0, end - start) if end else 1
                    elif len(for_node.iter.args) == 3:
                        # range(start, end, step)
                        start = self._extract_numeric_value(for_node.iter.args[0]) or 0
                        end = self._extract_numeric_value(for_node.iter.args[1])
                        step = self._extract_numeric_value(for_node.iter.args[2]) or 1
                        if end and step > 0:
                            return max(0, (end - start) // step)
                        return 1
                elif for_node.iter.func.id == 'len':
                    # for item in some_list: assume average list length
                    return 5  # Conservative estimate
        elif isinstance(for_node.iter, ast.Name):
            # for item in some_variable: check if we know the length
            var_name = for_node.iter.id
            if var_name in self.variable_assignments:
                return self.variable_assignments[var_name]
            # Common variable names that might be lists
            if 'list' in var_name.lower() or 'temps' in var_name.lower():
                return 5  # Conservative estimate for list variables
        return 1  # Default fallback
        
    def _extract_numeric_value(self, node):
        """Extract numeric value from AST node"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            # Try to convert string to float
            try:
                return float(node.s)
            except ValueError:
                return 0
        elif isinstance(node, ast.Name):
            # Variable - we can't evaluate it statically
            return 0
        elif isinstance(node, ast.BinOp):
            # Simple arithmetic
            left = self._extract_numeric_value(node.left)
            right = self._extract_numeric_value(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right if right != 0 else 0
        return 0