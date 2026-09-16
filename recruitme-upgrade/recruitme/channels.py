"""Employer-service preparation and consented imports. Intentionally no HTTP client."""
import argparse,datetime,json
from pathlib import Path
from .budget import StopRun

CHANNELS={
 'worksource_atlanta':{'url':'https://worksourceatlanta.org/programs-and-services-for-employers/',
  'account_url':'https://dol.georgia.gov/employment-services-registration',
  'mode':'employer_referral','cost_usd':'0','status':'EMPLOYER_REGISTRATION_REQUIRED',
  'requirements':['employer registration','service-area eligibility','worker consent to referral']},
 'bluerecruit':{'url':'https://bluerecruit.us/employers/',
  'account_url':'https://bluerecruit.us/employers/',
  'mode':'manual_employer_account','cost_usd':'0','monthly_connections':3,
  'status':'DIRECT_EMPLOYER_ELIGIBILITY_AND_ACCOUNT_REQUIRED',
  'requirements':['direct employer, not recruiter/RPO/staffing firm','free plan confirmed','worker consent / permitted export']}
}
REQUIRED=('employer_name','work_location','pay_range','role','commercial_tasks','minimum_experience','schedule','start_date','travel_radius')

def prepare(brief):
    if not isinstance(brief,dict) or set(brief)-set(REQUIRED):raise StopRun('Unknown employer brief fields')
    if any(not isinstance(v,str) or len(v)>1000 for v in brief.values()):raise StopRun('Invalid employer brief')
    return {'channels':CHANNELS,'brief':brief,'missing_fields':[k for k in REQUIRED if not brief.get(k)],
            'outreach_enabled':False,'automated_site_access':False,
            'next_action':'Human completes employer registration and permissions; no submission performed',
            'qualification':'Strong electrical fit AND attributable recent employment-change interest; no automatic A/B'}

def validate_import(job):
    channel=job.get('channel')
    if channel not in CHANNELS:raise StopRun('Unknown employer channel')
    if job.get('access_confirmed_by_human') is not True or job.get('retention_permission_confirmed') is not True:
        raise StopRun('Employer access and retention permission require human confirmation')
    if channel=='bluerecruit' and (job.get('direct_employer') is not True or job.get('free_plan_confirmed') is not True):
        raise StopRun('BlueRecruit free direct-employer eligibility required')
    records=job.get('candidates',[])
    if not isinstance(records,list) or len(records)>25:raise StopRun('Bounded candidate import required')
    for record in records:
        if record.get('reviewed_by_human') is not True or record.get('consented_referral') is not True or not record.get('source_record_id'):
            raise StopRun('Import requires human review, source ID and consented referral')
        if record.get('assessment',{}).get('classification') in ('A','B'):
            a=record['assessment']
            if not all(a.get(k) is True for k in ('signal_subject_confirmed','signal_date_verified','contradictions_checked')):
                raise StopRun('A/B requires attributed dated signal and contradiction review')
    return records

def main():
    p=argparse.ArgumentParser(description='Prepare employer referral packet locally; never sends or registers.')
    p.add_argument('--brief',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();brief=json.loads(a.brief.read_text()) if a.brief else {}
    packet=prepare(brief)
    # Exclusive creation prevents accidental loss of an existing completed packet.
    with a.output.open('x',encoding='utf-8') as f:json.dump(packet,f,indent=2)
    print('Employer packet prepared. No account created, site accessed or message sent.')

if __name__=='__main__':main()
