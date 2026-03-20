import React, { Fragment } from 'react';
import { IonButton } from '@ionic/react';
import { useAudio } from './context';

export const NormalizeButton: React.FC = () => {
  const audio = useAudio();

  if (!audio.source) return <Fragment />;

  return (
    <IonButton
      color={audio.normalize ? 'success' : 'medium'}
      shape="round"
      onClick={audio.toggleNormalize}
      title="Normalize audio level"
    >
      Normalize
    </IonButton>
  );
};
