"""Shared, offline store handoff checks; no credentials or provider clients."""
from __future__ import annotations
import datetime as dt
import re
from urllib.parse import urlparse, parse_qs


def check_input(rule, value, context, api):
    require = api['require']
    data = value['inputs']
    platform = rule['platform']
    pattern = r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+' if platform == 'apple' else r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+'
    require(re.fullmatch(pattern, data['application_id']),
            'store: application_id must be a bundle/package identifier')
    if platform == 'apple':
        require(re.fullmatch(r'[0-9]+', data['app_id']), 'store: expected App Store Connect numeric app ID')
        require(re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,2}', data['build_number']), 'store: invalid Apple build number')
    else:
        require(data['app_id'] == data['application_id'], 'store: Android app ID must equal package identifier')
        require(data['build_number'].isdigit() and 0 < int(data['build_number']) <= 2100000000,
                'store: invalid Android version code')
    require(0 <= data['rollout_percent'] <= 100, 'store: invalid rollout percentage')
    require(all(re.fullmatch(r'[A-Z]{2}', c) for c in data['countries']), 'store: expected ISO country codes')
    for ref in data['credential_refs']:
        require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_./-]{0,127}', ref['name']),
                'store: credential reference must be a logical name, never a value or credential file')
        require(not ref['name'].startswith(('ghp_', 'github_pat_', 'sk-', 'AKIA', 'ASIA', 'ya29.', 'AIza')),
                'store: credential-like value in reference')
        if ref['provider'] == 'env':
            require(re.fullmatch(r'[A-Z][A-Z0-9_]*', ref['name']), 'store: env credential reference must be an environment variable name')
    if data['artifact'] is not None:
        path = api['reference'](data['artifact'], context['base'])
        allowed = (('.pkg',) if data['platform_variant'] == 'macos' else ('.ipa',)) if platform == 'apple' else ('.aab',)
        require(path.suffix.lower() in allowed,
                'store: expected exported Apple artifact or Android App Bundle; no credentials')
    stage, track = data['target_stage'], data['track']
    fixed = ({'prepare': 'none', 'upload': 'none', 'testflight-internal': 'testflight-internal',
              'testflight-external': 'testflight-external', 'submit-review': 'app-store', 'production': 'app-store'}
             if platform == 'apple' else {'prepare': 'none', 'upload': 'none', 'play-internal': 'internal',
                                         'play-open': 'beta', 'production': 'production'})
    if stage in fixed:
        require(track == fixed[stage], 'store: stage and track disagree')
    else:
        require(track not in ('none', 'internal', 'beta', 'production'), 'store: expected actual closed-track ID')


def readback(key, result, value, context, rule, api, *, testing=False):
    require, fields = api['require'], api['fields']
    require(key is not None and key in context['evidence'], 'store: missing store readback')
    item = context['evidence'][key]
    require(item['kind'] == 'artifact', 'store: readback must be structured artifact evidence')
    record = api['load'](item['path'])
    identity = ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision')
    fields(record, 'kind platform artifact_sha256 stage track observed_at source native_status distribution_status '
           'review_status testers_configured tester_access_verified external_eligible compliance_complete '
           'production_access rollout_percent countries audience public_url ' + ' '.join(identity), 'store readback')
    require(record['kind'] == 'ct-store-readback.v1' and record['platform'] == rule['platform'], 'store: wrong readback kind/platform')
    data = value['inputs']
    for field in identity:
        require(record[field] == data[field], f'store: wrong readback {field}')
    require(record['artifact_sha256'] == data['artifact']['sha256'], 'store: wrong artifact in readback')
    api['timestamp'](record['observed_at'])
    observed = dt.datetime.fromisoformat(record['observed_at'].replace('Z', '+00:00'))
    require((dt.datetime.now(dt.timezone.utc) - observed).total_seconds() <= 3600, 'store: refresh stale readback')
    api['text'](record['source'], 'store.source')
    require(record['public_url'] is None or isinstance(record['public_url'], str), 'store: invalid public URL')
    source = urlparse(record['source'])
    hosts = ('appstoreconnect.apple.com', 'api.appstoreconnect.apple.com', 'apps.apple.com') if rule['platform'] == 'apple' else ('play.google.com', 'androidpublisher.googleapis.com')
    require(source.scheme == 'https' and source.hostname in hosts and not source.username and not source.password
            and not source.query and not source.fragment, 'store: source must be a sanitized provider HTTPS URL')
    for field in ('native_status', 'stage', 'track'):
        api['text'](record[field], 'store.' + field)
    for field in ('testers_configured', 'tester_access_verified', 'compliance_complete', 'production_access'):
        require(type(record[field]) is bool, 'store: invalid boolean ' + field)
    require(record['external_eligible'] is None or type(record['external_eligible']) is bool, 'store: invalid external eligibility')
    require(record['review_status'] in ('not-required', 'not-submitted', 'pending', 'approved', 'rejected'), 'store: unknown review status')
    require(record['distribution_status'] in ('processing', 'uploaded', 'available', 'submitted', 'published', 'draft', 'halted'), 'store: unknown distribution status')
    api['strings'](record['countries'], 'readback.countries')
    api['strings'](record['audience'], 'readback.audience', 1)
    require(type(record['rollout_percent']) in (int, float) and 0 <= record['rollout_percent'] <= 100, 'store: invalid readback rollout')
    phase = record['stage']
    testing_phases = ('testflight-internal', 'testflight-external') if rule['platform'] == 'apple' else ('play-internal', 'play-closed', 'play-open')
    if testing:
        require(phase in testing_phases, 'store: production needs testing readback for this candidate')
        # Historical testing can have a different audience/rollout from production.
        probe = dict(value, inputs=dict(data, target_stage=phase, track=record['track']))
        check_input(rule, probe, context, api)
    else:
        require(phase == data['target_stage'] and record['track'] == data['track'], 'store: wrong requested stage/track')
        for field in ('audience', 'countries', 'rollout_percent'):
            require(record[field] == data[field], 'store: release scope changed: ' + field)
    if phase != 'upload':
        require(record['compliance_complete'], 'store: unresolved compliance')
    if rule['platform'] == 'apple':
        require(record['external_eligible'] is True, 'store: Internal Only build is ineligible')
    if phase in testing_phases:
        require(record['distribution_status'] == 'available' and record['testers_configured'] and record['tester_access_verified'],
                'store: tester configuration/invitation alone is not verified access')
        require(record['review_status'] in ('approved', 'not-required'), 'store: testing review incomplete')
        if rule['platform'] == 'apple':
            require(record['native_status'] in ('Testing', 'IN_BETA_TESTING'),
                    'store: native status does not prove testing availability')
        if rule['platform'] == 'android':
            require(record['native_status'] in ('completed', 'inProgress'), 'store: Play release not rolled out')
            if phase == 'play-open':
                require(record['production_access'], 'store: open testing eligibility not confirmed')
    elif phase == 'upload':
        require(record['distribution_status'] in ('uploaded', 'processing'), 'store: upload receipt must not claim a later milestone')
    elif phase == 'submit-review':
        require(record['distribution_status'] == 'submitted' and record['review_status'] == 'pending', 'store: draft is not submitted review')
        require(record['native_status'] in ('WAITING_FOR_REVIEW', 'IN_REVIEW', 'Waiting for Review', 'In Review'), 'store: review submission not confirmed')
    elif phase == 'production':
        require(record['distribution_status'] == 'published' and record['review_status'] in ('approved', 'not-required')
                and record['production_access'] and record['rollout_percent'] > 0 and bool(record['countries']), 'store: production not available')
        public = urlparse(record['public_url'] or '')
        require(public.scheme == 'https' and not public.username and not public.password and not public.fragment, 'store: missing public store URL')
        if rule['platform'] == 'apple':
            require(public.hostname == 'apps.apple.com' and not public.query and public.path.endswith('/id' + data['app_id']), 'store: wrong Apple storefront URL')
            require(record['review_status'] == 'approved' and record['native_status'] in ('READY_FOR_DISTRIBUTION', 'READY_FOR_SALE', 'Ready for Distribution', 'Ready for Sale'), 'store: App Store approval/availability missing')
        else:
            require(public.hostname == 'play.google.com' and public.path == '/store/apps/details'
                    and parse_qs(public.query) == {'id': [data['application_id']]}, 'store: wrong Play storefront URL')
            require(record['native_status'] in ('completed', 'inProgress'), 'store: Play production not rolled out')
    else:
        raise ValueError('store: unexpected provider-readback stage')
    if rule['platform'] == 'android' and phase != 'upload':
        require((record['native_status'] == 'completed' and record['rollout_percent'] == 100)
                or (record['native_status'] == 'inProgress' and 0 < record['rollout_percent'] < 100), 'store: Play rollout fraction contradicts status')
    return record


def decision(source_id, kind, rule, value, context, api):
    require = api['require']
    require(source_id is not None and source_id in context['source'], 'store: decision source missing')
    record = api['load'](context['source'][source_id])
    common = 'kind platform platform_variant app_id application_id version build_number candidate_revision artifact_sha256 source observed_at '
    api['fields'](record, common + ('authorized target_stage track audience countries rollout_percent' if kind == 'authorization' else 'accepted'), 'store decision')
    require(record['kind'] == 'ct-store-' + kind + '.v1' and record['platform'] == rule['platform'], 'store: wrong decision kind/platform')
    data = value['inputs']
    for field in ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision'):
        require(record[field] == data[field], 'store: decision candidate mismatch: ' + field)
    require(record['artifact_sha256'] == data['artifact']['sha256'], 'store: decision artifact mismatch')
    api['text'](record['source'], 'decision source')
    api['timestamp'](record['observed_at'])
    if kind == 'authorization':
        require(record['authorized'] is True, 'store: action was not authorized')
        for field in ('target_stage', 'track', 'audience', 'countries', 'rollout_percent'):
            require(record[field] == data[field], 'store: authorization scope mismatch: ' + field)
    else:
        require(record['accepted'] is True, 'store: candidate was not accepted')


def check_output(rule, result, value, context, api):
    require = api['require']
    data = value['inputs']
    require(data['artifact'] is not None, 'store: release artifact is missing')
    require(result['artifact_sha256'] == data['artifact']['sha256'], 'store: output artifact digest mismatch')
    stage = data['target_stage']
    if stage == 'prepare':
        require(result['store_readback'] is None and result['testing_readback'] is None, 'store: prepare must not claim provider milestones')
    else:
        require(data['authorization_source'] is not None and data['authorized_stage'] == stage, 'store: scoped authorization source required')
        decision(data['authorization_source'], 'authorization', rule, value, context, api)
        readback(result['store_readback'], result, value, context, rule, api)
    if stage == 'production':
        require(result['acceptance_source'] is not None, 'store: candidate-bound human acceptance required')
        decision(result['acceptance_source'], 'acceptance', rule, value, context, api)
        readback(result['testing_readback'], result, value, context, rule, api, testing=True)
    if data['require_device_proof'] or result['device_proof'] is not None:
        key = result['device_proof']
        require(key is not None and key in context['evidence'], 'store: installed-device proof required')
        item = context['evidence'][key]
        require(item['kind'] == 'artifact', 'store: device proof must be a structured artifact')
        proof = api['load'](item['path'])
        api['fields'](proof, 'kind platform platform_variant app_id application_id version build_number artifact_sha256 candidate_revision observed_at installed smoke_passed limitations', 'device proof')
        require(proof['kind'] == 'ct-device-proof.v1' and proof['platform'] == rule['platform'], 'store: wrong device proof kind/platform')
        for field in ('platform_variant', 'app_id', 'application_id', 'version', 'build_number', 'candidate_revision'):
            require(proof[field] == data[field], 'store: wrong device candidate: ' + field)
        require(proof['artifact_sha256'] == data['artifact']['sha256'] and proof['installed'] is True and proof['smoke_passed'] is True, 'store: installation/smoke not proven')
        api['timestamp'](proof['observed_at'])
        api['strings'](proof['limitations'], 'device limitations', 1)
