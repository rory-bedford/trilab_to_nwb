Note this job requires your database credentials. You can provide them as environment variables using:

```
export DB_USER=your_username
export DB_PASS=your_password
sbatch --export=DB_USER,DB_PASS stefan_upload.slurm
```
