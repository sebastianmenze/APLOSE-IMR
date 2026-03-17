# Generated migration for simplified NetCDF dataset architecture
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0097_auto_20260105_1711'),
    ]

    operations = [
        # Add new fields for simple NetCDF structure
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='sample_rate',
            field=models.FloatField(default=48000, help_text='Sample rate in Hz'),
        ),
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='nfft',
            field=models.IntegerField(default=2048, help_text='FFT size'),
        ),
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='hop_length',
            field=models.IntegerField(default=512, help_text='Hop length for STFT'),
        ),
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='duration',
            field=models.FloatField(default=0.0, help_text='Duration in seconds'),
        ),
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='frequency_min',
            field=models.FloatField(default=0.0, help_text='Minimum frequency in Hz'),
        ),
        migrations.AddField(
            model_name='spectrogramanalysis',
            name='frequency_max',
            field=models.FloatField(default=24000.0, help_text='Maximum frequency in Hz'),
        ),

        # Make old fields optional for backwards compatibility
        migrations.AlterField(
            model_name='spectrogramanalysis',
            name='fft',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='spectrogram_analysis',
                to='api.fft'
            ),
        ),
        migrations.AlterField(
            model_name='spectrogramanalysis',
            name='colormap',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='spectrogram_analysis',
                to='api.colormap'
            ),
        ),
        migrations.AlterField(
            model_name='spectrogramanalysis',
            name='dynamic_min',
            field=models.FloatField(default=0.0, help_text='Minimum value for display'),
        ),
        migrations.AlterField(
            model_name='spectrogramanalysis',
            name='dynamic_max',
            field=models.FloatField(default=100.0, help_text='Maximum value for display'),
        ),

        # Remove the legacy constraint
        migrations.RemoveConstraint(
            model_name='spectrogramanalysis',
            name='spectrogram_analysis_legacy',
        ),
    ]
