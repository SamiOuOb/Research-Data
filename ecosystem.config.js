module.exports = {
  apps : [{
    name: 'probemon',
    script: 'python probemon.py -i mon1 -r -s -f -l',
    watch: './probemon.py',
    cron_restart: '0 0 * * *',    
  }]
};
