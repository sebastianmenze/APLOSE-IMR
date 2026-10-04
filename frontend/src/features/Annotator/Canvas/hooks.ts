import { useAnnotatorCanvasContext } from './context';
import { useCallback } from 'react';
import { useWindowContainerWidth } from '@/features/Annotator/Canvas/window.hooks';
import { useTimeScale } from '@/features/Annotator/Axis';


export const useFocusCanvasOnTime = () => {
  const timeScale = useTimeScale()
  const containerWidth = useWindowContainerWidth()
  const {
    mainCanvasRef,
  } = useAnnotatorCanvasContext()

  return useCallback((time: number) => {
    const left = timeScale.valueToPosition(time) - containerWidth / 2;
    mainCanvasRef?.current?.parentElement?.scrollTo({ left })
  }, [ timeScale, containerWidth ])
}
