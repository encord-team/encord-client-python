"""Public camera intrinsics types and convenience constructors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence, Union

from encord.beta.scene.internal.upload import CameraIntrinsicsAdvanced as _CameraIntrinsicsAdvanced
from encord.beta.scene.internal.upload import CameraIntrinsicsSimple as _CameraIntrinsicsSimple
from encord.beta.scene.internal.upload import DivisionDistortionModel as _DivisionDistortionModel
from encord.beta.scene.internal.upload import FishEyeDistortionModel as _FishEyeDistortionModel
from encord.beta.scene.internal.upload import PinholeDistortionModel as _PinholeDistortionModel
from encord.beta.scene.internal.upload import PlumbBobDistortionModel as _PlumbBobDistortionModel
from encord.beta.scene.internal.upload import RadialDistortionModel as _RadialDistortionModel
from encord.beta.scene.internal.upload import RationalPolynomialDistortionModel as _RationalPolynomialDistortionModel
from encord.beta.scene.internal.upload import UCMDistortionModel as _UCMDistortionModel

_INTRINSICS_EXTRA_FIELDS = frozenset({"dfx", "dfy", "dox", "doy", "skew"})

_DISTORTION_MODEL_MAP: dict[str, Any] = {
    "radial": _RadialDistortionModel,
    "plumb_bob": _PlumbBobDistortionModel,
    "fisheye": _FishEyeDistortionModel,
    "rational_polynomial": _RationalPolynomialDistortionModel,
    "pinhole": _PinholeDistortionModel,
    "division": _DivisionDistortionModel,
    "ucm": _UCMDistortionModel,
}


@dataclass
class SimpleIntrinsics:
    """Simple camera intrinsics (focal length + principal point).

    Prefer the dedicated constructors (:func:`intrinsics_pinhole`,
    :func:`intrinsics_radial`, :func:`intrinsics_plumb_bob`,
    :func:`intrinsics_fisheye`) or the generic :func:`intrinsics_simple`
    rather than instantiating this class directly.

    The ``extra`` dict holds distortion coefficients and optional fields.
    Distortion coefficients are model-specific. The following optional
    fields apply to all models: ``dfx``, ``dfy``, ``dox``, ``doy``, ``skew``.
    """

    fx: float
    fy: float
    ox: float
    oy: float
    model: str | None = None
    extra: dict[str, float] = field(default_factory=dict, repr=False)

    def _to_internal(self) -> _CameraIntrinsicsSimple:
        distortion_model = None
        if self.model is not None:
            model_params = {k: v for k, v in self.extra.items() if k not in _INTRINSICS_EXTRA_FIELDS}
            cls = _DISTORTION_MODEL_MAP.get(self.model)
            if cls is not None:
                distortion_model = cls.model_construct(type=self.model, **model_params)

        return _CameraIntrinsicsSimple.model_construct(
            type="simple",
            fx=self.fx,
            fy=self.fy,
            ox=self.ox,
            oy=self.oy,
            model=distortion_model,
            dfx=self.extra.get("dfx"),
            dfy=self.extra.get("dfy"),
            dox=self.extra.get("dox"),
            doy=self.extra.get("doy"),
            skew=self.extra.get("skew"),
        )


@dataclass
class AdvancedIntrinsics:
    """Advanced camera intrinsics (full calibration matrices).

    .. warning::
       In most cases :class:`SimpleIntrinsics` (via
       :func:`intrinsics_simple` or one of the dedicated constructors)
       is sufficient and much easier to work with. Only use advanced
       intrinsics when you have pre-computed full K / R / P calibration
       matrices and genuinely need to supply them directly.

    Prefer :func:`intrinsics_advanced` rather than instantiating this
    class directly.

    Args:
        k: 9-element intrinsic camera matrix (row-major 3x3).
            Validated to have exactly 9 elements at build time.
        r: 9-element rectification matrix (row-major 3x3).
            Validated to have exactly 9 elements at build time.
        p: 12-element projection matrix (row-major 3x4).
            Validated to have exactly 12 elements at build time.
        model: Optional distortion model name.
    """

    k: Sequence[float] | None = None
    r: Sequence[float] | None = None
    p: Sequence[float] | None = None
    model: str | None = None

    def _to_internal(self) -> _CameraIntrinsicsAdvanced:
        distortion_model = None
        if self.model is not None:
            cls = _DISTORTION_MODEL_MAP.get(self.model)
            if cls is not None:
                distortion_model = cls.model_construct(type=self.model)

        return _CameraIntrinsicsAdvanced.model_construct(
            type="advanced",
            model=distortion_model,
            k=list(self.k) if self.k is not None else None,
            r=list(self.r) if self.r is not None else None,
            p=list(self.p) if self.p is not None else None,
            skew=None,
        )


Intrinsics = Union[SimpleIntrinsics, AdvancedIntrinsics]


def intrinsics_simple(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    model: str | None = None,
    **kwargs: float,
) -> SimpleIntrinsics:
    """Build simple camera intrinsics (focal length + principal point).

    For models without a dedicated constructor, pass the model name and
    its coefficients as keyword arguments::

        intrinsics_simple(fx, fy, ox, oy, model="division", k=0.01)
        intrinsics_simple(fx, fy, ox, oy, model="ucm", xi=0.5, k1=0.1, k2=0.0, k3=0.0)

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        model: Optional distortion model name.
        **kwargs: Distortion coefficients and optional extra fields.
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model=model, extra=dict(kwargs))


def intrinsics_advanced(
    k: Sequence[float] | None = None,
    r: Sequence[float] | None = None,
    p: Sequence[float] | None = None,
    *,
    model: str | None = None,
) -> AdvancedIntrinsics:
    """Build advanced camera intrinsics using full calibration matrices.

    .. warning::
       In most cases :func:`intrinsics_simple` (or one of the dedicated
       constructors) is sufficient. Only reach for advanced intrinsics
       when you have pre-computed K / R / P matrices.

    Args:
        k: 9-element intrinsic camera matrix (row-major 3x3).
        r: 9-element rectification matrix (row-major 3x3).
        p: 12-element projection matrix (row-major 3x4).
        model: Optional distortion model name.
    """
    return AdvancedIntrinsics(k=k, r=r, p=p, model=model)


def intrinsics_pinhole(fx: float, fy: float, ox: float, oy: float) -> SimpleIntrinsics:
    """Build pinhole intrinsics (no distortion coefficients).

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model="pinhole")


def intrinsics_radial(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a radial distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First radial distortion coefficient.
        k2: Second radial distortion coefficient.
        k3: Third radial distortion coefficient.
    """
    return SimpleIntrinsics(fx=fx, fy=fy, ox=ox, oy=oy, model="radial", extra={"k1": k1, "k2": k2, "k3": k3})


def intrinsics_plumb_bob(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
    t1: float,
    t2: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a plumb-bob (Brown-Conrady) distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First radial distortion coefficient.
        k2: Second radial distortion coefficient.
        k3: Third radial distortion coefficient.
        t1: First tangential distortion coefficient.
        t2: Second tangential distortion coefficient.
    """
    return SimpleIntrinsics(
        fx=fx,
        fy=fy,
        ox=ox,
        oy=oy,
        model="plumb_bob",
        extra={"k1": k1, "k2": k2, "k3": k3, "t1": t1, "t2": t2},
    )


def intrinsics_fisheye(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
    k4: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a fisheye (Kannala-Brandt) distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First distortion coefficient.
        k2: Second distortion coefficient.
        k3: Third distortion coefficient.
        k4: Fourth distortion coefficient.
    """
    return SimpleIntrinsics(
        fx=fx,
        fy=fy,
        ox=ox,
        oy=oy,
        model="fisheye",
        extra={"k1": k1, "k2": k2, "k3": k3, "k4": k4},
    )


def intrinsics_rational_polynomial(
    fx: float,
    fy: float,
    ox: float,
    oy: float,
    *,
    k1: float,
    k2: float,
    k3: float,
    k4: float,
    k5: float,
    k6: float,
    t1: float,
    t2: float,
) -> SimpleIntrinsics:
    """Build intrinsics with a rational-polynomial distortion model.

    Args:
        fx: Focal length along the *x*-axis (pixels).
        fy: Focal length along the *y*-axis (pixels).
        ox: Principal-point *x* offset (pixels).
        oy: Principal-point *y* offset (pixels).
        k1: First radial distortion coefficient.
        k2: Second radial distortion coefficient.
        k3: Third radial distortion coefficient.
        k4: Fourth radial distortion coefficient.
        k5: Fifth radial distortion coefficient.
        k6: Sixth radial distortion coefficient.
        t1: First tangential distortion coefficient.
        t2: Second tangential distortion coefficient.
    """
    return SimpleIntrinsics(
        fx=fx,
        fy=fy,
        ox=ox,
        oy=oy,
        model="rational_polynomial",
        extra={"k1": k1, "k2": k2, "k3": k3, "k4": k4, "k5": k5, "k6": k6, "t1": t1, "t2": t2},
    )
