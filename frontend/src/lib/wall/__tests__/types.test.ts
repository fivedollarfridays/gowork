import { describe, it, expectTypeOf } from "vitest";
import type {
  TimePhase,
  AccentShift,
  ChapterId,
  ChapterState,
  MapboxLayer,
  CameraState,
  SoundId,
  LocaleCode,
  BarrierType,
  BarrierGraphNode,
} from "../types";

describe("lib/wall/types (T1.67)", () => {
  it("TimePhase is a 4-value union", () => {
    expectTypeOf<TimePhase>().toEqualTypeOf<"morning" | "day" | "evening" | "night">();
  });

  it("AccentShift is a 4-value union", () => {
    expectTypeOf<AccentShift>().toEqualTypeOf<"cyan" | "amber" | "rose" | "navy">();
  });

  it("ChapterId is a 1..10 numeric literal union", () => {
    expectTypeOf<ChapterId>().toEqualTypeOf<1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10>();
  });

  it("ChapterState contains id + camera + accent fields", () => {
    expectTypeOf<ChapterState>().toMatchTypeOf<{
      id: ChapterId;
      camera: CameraState;
      accentShift: AccentShift;
    }>();
  });

  it("MapboxLayer has id+type+source", () => {
    expectTypeOf<MapboxLayer>().toMatchTypeOf<{
      id: string;
      type: string;
      source: string;
    }>();
  });

  it("CameraState has the 5 mapbox view-state fields", () => {
    expectTypeOf<CameraState>().toMatchTypeOf<{
      lng: number;
      lat: number;
      zoom: number;
      pitch: number;
      bearing: number;
    }>();
  });

  it("SoundId mirrors the audio module union", () => {
    expectTypeOf<SoundId>().toEqualTypeOf<
      "footstep" | "paper-rustle" | "calculator-click" | "chime" | "wind-ambient"
    >();
  });

  it("LocaleCode is en or es", () => {
    expectTypeOf<LocaleCode>().toEqualTypeOf<"en" | "es">();
  });

  it("BarrierType covers the 4 W3 barriers", () => {
    expectTypeOf<BarrierType>().toEqualTypeOf<
      "criminal-record" | "transit" | "childcare" | "credit"
    >();
  });

  it("BarrierGraphNode has id+type+severity", () => {
    expectTypeOf<BarrierGraphNode>().toMatchTypeOf<{
      id: string;
      type: BarrierType;
      severity: number;
    }>();
  });
});
