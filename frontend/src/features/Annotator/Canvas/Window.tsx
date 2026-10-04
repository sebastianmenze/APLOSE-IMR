import React from 'react';
import styles from './styles.module.scss';
import { AcousticFeatures } from '@/features/Annotator/Annotation';
import { NetCDFSpectrogram } from '@/features/Annotator/Spectrogram';

export const AnnotatorCanvasWindow: React.FC = () => {
  return <div className={ styles.spectrogramWindow }>

    <div className={ styles.spectrogram }>
      <NetCDFSpectrogram/>
    </div>

    <AcousticFeatures/>

  </div>
}
