from jinja2 import nodes, parser


class Parser(parser.Parser):

    def parse_filter(self, node, start_inline=False):
        while self.stream.current.type == 'pipe' or start_inline:
            if not start_inline:
                next(self.stream)
            token = self.stream.expect('name')
            name = token.value
            while self.stream.current.type == 'dot':
                next(self.stream)
                name += '.' + self.stream.expect('name').value
            if self.stream.current.type == 'lparen':
                args, kwargs, dyn_args, dyn_kwargs = self.parse_call(None)
            elif self.stream.current.type == 'colon':
                next(self.stream)
                args = [self.parse_primary()]
                kwargs = []
                dyn_args = dyn_kwargs = None
            else:
                args = []
                kwargs = []
                dyn_args = dyn_kwargs = None
            node = nodes.Filter(node, name, args, kwargs, dyn_args,
                                dyn_kwargs, lineno=token.lineno)
            start_inline = False
        return node