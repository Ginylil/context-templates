"""Class-specific view coverage, degree limits and offline camera composition."""
import base64
import html
import json
import re
from pathlib import Path

ID = re.compile(r'[a-z][a-z0-9-]{0,63}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def views_for(model):
    return model.get('views', [{'id': 'structure', 'label': 'Class diagram',
                               'nodes': [n['id'] for n in model['nodes']],
                               'edges': [e['id'] for e in model['edges']]}])


def validate(model):
    nodes = {n['id'] for n in model['nodes']}
    edges = {e['id']: e for e in model['edges']}
    views = views_for(model)
    require(isinstance(views, list) and views, 'class.views: provide linked diagram views')
    ids, covered_nodes, covered_edges = set(), set(), set()
    for view in views:
        require(isinstance(view, dict), 'class.view: expected an object')
        identity = view.get('id')
        require(isinstance(identity, str) and ID.fullmatch(identity) and identity not in ids,
                'class.view: invalid or duplicate id')
        ids.add(identity)
        require(isinstance(view.get('label'), str) and 0 < len(view['label'].strip()) <= 100,
                'class.view: provide a concise label')
        for key, allowed in [('nodes', nodes), ('edges', edges)]:
            values = view.get(key)
            require(isinstance(values, list) and all(isinstance(x, str) and x in allowed for x in values)
                    and len(values) == len(set(values)), f'class.view.{key}: unknown or duplicate identifier')
        require(view['nodes'], 'class.view: include at least one class')
        degree = {}
        for identity in view['edges']:
            edge = edges[identity]
            require(edge['from'] in view['nodes'] and edge['to'] in view['nodes'],
                    'class.view: relationship endpoints must belong to the view')
            for endpoint in (edge['from'], edge['to']):
                degree[endpoint] = degree.get(endpoint, 0) + 1
        require(all(value <= 20 for value in degree.values()),
                'class.view: split classes above 20 relationships into linked diagram views')
        covered_nodes.update(view['nodes']); covered_edges.update(view['edges'])
    require(covered_nodes == nodes and covered_edges == set(edges),
            'class.views: every class and relationship must remain represented')
    for scenario in model['scenarios']:
        for step in scenario['steps']:
            focus = step.get('focus', step['nodes'][0])
            require(isinstance(focus, str) and focus in step['nodes'],
                    'class.step.focus: select one of the highlighted classes')
            candidates = [view for view in views if set(step['nodes']) <= set(view['nodes'])
                          and set(step['edges']) <= set(view['edges'])]
            require(candidates, 'class.step: highlighted classes and relationships must fit one linked view')
            if 'view' in step:
                require(isinstance(step['view'], str) and any(v['id'] == step['view'] for v in candidates),
                        'class.step.view: unknown or incompatible linked view')


def render(model):
    assets = Path(__file__).resolve().parents[1] / 'assets'
    folder = assets / 'class-camera'
    page = (folder / 'template.html').read_text(encoding='utf-8')
    for key, filename in [('STYLES', 'styles.css'), ('ADAPTER', 'adapter.js'),
                          ('LAYOUT', 'layout.js'), ('ROUTING', 'routing.js'),
                          ('VIEW', 'view.js'), ('CAMERA', 'camera.js'),
                          ('INPUT', 'input.js'), ('TOUR', 'tour.js')]:
        marker = f'__{key}__\n'
        require(page.count(marker) == 1, f'class template: expected one {key} fragment')
        content = (folder / filename).read_text(encoding='utf-8')
        require(content.endswith('\n'), f'class fragment: {filename} must end with newline')
        page = page.replace(marker, content)
    data = json.dumps(model, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    data = data.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    logo = 'data:image/png;base64,' + base64.b64encode((assets / 'ginylil.png').read_bytes()).decode('ascii')
    values = {'__PAGE_TITLE__': html.escape(model['title']), '__DIAGRAM_DATA__': data, '__LOGO__': logo}
    return re.sub(r'__PAGE_TITLE__|__DIAGRAM_DATA__|__LOGO__', lambda m: values[m[0]], page)
