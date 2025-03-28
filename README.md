# trackerMetaManager
a clone of metaManager to recode for move to HCA tracker site

## Notes

- Adaptation of this code is currently a work in progress. The description in `docs` is no longer entirely accurate.
- The script can currently be run by editing the `folder_id` variable in `metadata_correctness_plotting_crontab.py`, setting the `GOOGLE_SERVICE_ACCOUNT` environment variable, and running `poetry run pyCodebase/metadata_correctness_plotting_crontab.py`.
- The output images seem to have an issue where the labels are cut off.
- `run_tasks.sh` will no longer work due to `metadata_correctness_plotting_crontab.py` having been moved.
