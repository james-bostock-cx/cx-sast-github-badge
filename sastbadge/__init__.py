import logging
import os
from flask import Flask
from CheckmarxPythonSDK.CxRestAPISDK import ScansAPI

SCAN_STATUS_FINISHED = 7

def generate_badge(project_id, logger, scans_api=None):

    if not scans_api:
        scans_api = ScansAPI()

    badge = {
        'schemaVersion': 1,
        'label': 'Checkmarx',
        'labelColor': 'gray'
    }

    scans = scans_api.get_all_scans_for_project(project_id=project_id, last=1)
    if len(scans) != 1:
        logger.debug(f'No scans found for project {project_id}')
        badge['message'] = 'Unscanned'
        badge['color'] = 'Red'
        return badge

    scan = scans[0]
    logger.debug(f'Scan status: {scan.status}')
    if scan.status.id == SCAN_STATUS_FINISHED:
        stats = scans_api.get_statistics_results_by_scan_id(scan.id)
        logger.debug(f'Scan statistics: {stats}')
        if (stats.high_severity == 0 and
            stats.medium_severity == 0 and
            stats.low_severity == 0 and
            stats.info_severity == 0):
            badge['message'] = 'Passed'
            badge['color'] = 'green'
        else:
            badge['message'] = 'Failed'
            badge['color'] = 'red'
    else:
        badge['message'] = 'Scan not finished'
        badge['color'] = 'orange'

    logger.debug(f'Badge: {badge}')
    return badge


def create_app(test_config=None):

    app = Flask(__name__)

    log_level = os.environ.get('SAST_BADGE_LOG_LEVEL', 'WARN')
    app.logger.setLevel(log_level)
    # Without the following we get duplicate log messages
    app.logger.propagate = False

    @app.route('/badge/<project_id>')
    def badge(project_id):
        try:
            return generate_badge(int(project_id), app.logger)
        except Exception as e:
            print(e)
            return {
                    'schemaVersion': 1,
                    'label': 'Checkmarx',
                    'labelColor': 'gray',
                    'message': 'Server error',
                    'color': 'red'
                    }

    return app
