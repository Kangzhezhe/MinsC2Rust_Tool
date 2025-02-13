import os
import json

class DataManager:
    def __init__(self, source_path,include_dict,all_pointer_funcs,include_dict_without_fn_pointer):
        self.data = []
        self.source_names = [os.path.splitext(os.path.basename(f))[0] for f in source_path]
        self.include_dict = include_dict
        self.include_dict_without_fn_pointer = include_dict_without_fn_pointer
        self.all_pointer_funcs = all_pointer_funcs
        self.comment = "// 注意：该函数不允许修改，因为工程中其他文件中的函数也调用了他们，如果修改了，会影响其他文件内函数的功能，完整原样返回该函数\n"
        for f in source_path:
            with open(f, 'r') as file:
                self.data.append(json.load(file))

    def get_all_source(self,source_name,all_files,without_fn_pointer=False):
        if without_fn_pointer:
            child_source = self.include_dict_without_fn_pointer.get(source_name, [])
        else:
            child_source = self.include_dict.get(source_name, [])
        for source in child_source:
            if source not in all_files:
                all_files.append(source)
                self.get_all_source(source,all_files)
            
    def get_parent_sources(self, source_name, all_files):
        for parent, children in self.include_dict.items():
            if source_name in children and parent not in all_files:
                all_files.append(parent)
                self.get_parent_sources(parent, all_files)

    
    def get_include_indices(self,test_source_name,without_fn_pointer=False):
        all_include_files = [test_source_name]
        self.get_all_source(test_source_name,all_include_files,without_fn_pointer)
        include_files_indices = [self.source_names.index(file) for file in all_include_files if file in self.source_names]
        self.include_files_indices = include_files_indices
        self.all_include_files = all_include_files
        return include_files_indices,all_include_files

    
    def get_include_indices_with_parent(self, test_source_name):
        all_include_files = [test_source_name]
        self.get_all_source(test_source_name, all_include_files)
        for source in all_include_files.copy():
            self.get_parent_sources(source, all_include_files)
        for source in all_include_files.copy():
            self.get_all_source(source, all_include_files)
        include_files_indices = [self.source_names.index(file) for file in all_include_files if file in self.source_names]
        self.include_files_indices = include_files_indices
        self.all_include_files = all_include_files
        return include_files_indices, all_include_files

    def get_content(self, func_name):
        for i, jsonfile in enumerate(self.data):
            if func_name in jsonfile and i in self.include_files_indices:
                return jsonfile[func_name], jsonfile["extra"], i
        return "", "", -1

    def get_source_name_by_func_name(self, func_name):
        _, _, i = self.get_content(func_name)
        if i != -1 and i in self.include_files_indices:
            return self.source_names[i]
        else:
            return ''

    def get_result(self, func_name, results):
        for k, v in results.items() :
            if func_name in v and k in self.all_include_files:
                # if func_name  in self.all_pointer_funcs:
                #     return v[func_name].replace('\n', f'\n{self.comment}', 1)
                # else:
                return v[func_name]
        return ''

    def get_child_context(self, func_name, results, funcs_child):
        child_context = set()
        extra_contents = []
        source_name = self.get_source_name_by_func_name(func_name)
        extra_content = results[source_name].get('extra', '')
        if extra_content:
            extra_contents.append(extra_content)
        child_funs = ''
        if func_name in funcs_child:
            all_child_funs = self.get_all_child_functions(func_name, funcs_child)
            for child_fun in all_child_funs:
                if child_fun != func_name and self.get_result(child_fun, results) != '':
                    child_funs += child_fun + ","
                    extra = results[self.get_source_name_by_func_name(child_fun)].get('extra', '')
                    if extra and extra not in extra_contents:
                        extra_contents.append(extra)
                    # child_context.add(self.get_result(child_fun, results).lstrip().split('\n', 1)[0][:-1])
                    child_context.add(self.get_result(child_fun, results))
        child_context = '\n'.join(extra_contents + list(child_context))
        return child_context, child_funs

    def get_child_context_c(self, func_name, results, funcs_child):
        source_context, source_extra, i = self.get_content(func_name)
        child_context = source_context
        child_funs = func_name + ","
        if func_name in funcs_child:
            all_child_funs = self.get_all_child_functions(func_name, funcs_child)
            for child_fun in all_child_funs:
                if child_fun != func_name and self.get_result(child_fun, results) == '':
                    child_funs += child_fun + ","
                    source_context, source_extra, _ = self.get_content(child_fun)
                    child_context = child_context + '\n' + source_context
        return child_context, child_funs, ''

    def get_details(self, func_names):
        before_details = ''
        seen_details = set()
        for func_name in func_names:
            _, _, i = self.get_content(func_name)
            jsonfile = self.data[i]
            source_extra = jsonfile['extra']
            details_index = source_extra.find('extract_info')
            if details_index != -1:
                detail = source_extra[:details_index]
                if detail not in seen_details:
                    seen_details.add(detail)
                    before_details += '\n' + detail
        return before_details

    def get_all_child_functions(self, func_name, funcs_child):
        all_child_funs = set()

        def add_child_functions(func):
            if func in funcs_child:
                for child_fun in funcs_child[func]:
                    if child_fun not in all_child_funs:
                        all_child_funs.add(child_fun)
                        add_child_functions(child_fun)

        add_child_functions(func_name)
        return all_child_funs

    def get_all_parent_functions(self,func_name, funcs_child):
        all_parent_funs = set()

        def add_parent_functions(func):
            for parent, children in funcs_child.items():
                if func in children and parent not in all_parent_funs:
                    all_parent_funs.add(parent)
                    add_parent_functions(parent)

        add_parent_functions(func_name)
        return all_parent_funs
